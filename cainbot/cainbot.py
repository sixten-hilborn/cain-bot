# This example requires the 'message_content' intent.

import discord
import json
import typing
import enum
import datetime
import time
from discord.ext import tasks
from discord.ext import commands
from .d2runewizard import D2RunewizardClient

__version__ = '0.1.0'
client = None

act1_zones = [
    "Blood Moor and Den of Evil",
    "Cold Plains and The Cave",
    "Burial Grounds, The Crypt, and The Mausoleum",
    "Stony Field",
    "Tristram",
    "Dark Wood and Underground Passage",
    "Black Marsh and The Hole",
    "The Forgotten Tower",
    "The Pit",
    "Jail and Barracks",
    "Cathedral and Catacombs",
    "Moo Moo Farm",
]
act2_zones = [
    "Lut Gholein Sewers",
    "Rocky Waste and Stony Tomb",
    "Dry Hills and Halls of the Dead",
    "Far Oasis",
    "Lost City, Valley of Snakes, and Claw Viper Temple",
    "Ancient Tunnels",
    "Arcane Sanctuary",
    "Tal Rasha's Tombs and Tal Rasha's Chamber",
]
act3_zones = [
    "Spider Forest and Spider Cavern",
    "Great Marsh",
    "Flayer Jungle and Flayer Dungeon",
    "Kurast Bazaar, Ruined Temple, and Disused Fane",
    "Kurast Sewers",
    "Travincal",
    "Durance of Hate",
]
act4_zones = [
    "Outer Steppes and Plains of Despair",
    "River of Flame and City of the Damned",
    "The Chaos Sanctuary",
]
act5_zones = [
    "Bloody Foothills, Frigid Highlands, and Abaddon",
    "Glacial Trail and Drifter Cavern",
    "Crystalline Passage and Frozen River",
    "Arreat Plateau and Pit of Acheron",
    "Nihlathak's Temple, Halls of Anguish, Halls of Pain, and Halls of Vaught",
    "Ancient's Way and Icy Cellar",
    "Worldstone Keep, Throne of Destruction, and Worldstone Chamber",
]
all_zones = [
    act1_zones,
    act2_zones,
    act3_zones,
    act4_zones,
    act5_zones,
]

ladder_reset_dates = [
    datetime.date(2022, 4, 28),
    datetime.date(2022, 10, 6),
    datetime.date(2026, 8, 21),
]
runes = [
    'el', 'eld', 'tir', 'nef', 'eth', 'ith', 'tal', 'ral', 'ort', 'thul',
    'amn', 'sol', 'shael', 'dol', 'hel', 'io', 'lum', 'ko', 'fal', 'lem',
    'pul', 'um', 'mal', 'ist', 'gul', 'vex', 'ohm', 'lo', 'sur', 'ber',
    'jah', 'cham', 'zod'
]

POLL_TIMES = [
    datetime.time(hour=hour, minute=minute, second=15,
                  tzinfo=datetime.timezone.utc)
    for hour in range(24)
    for minute in (0, 30)
]


def main():
    intents = discord.Intents.default()
    intents.message_content = True

    client = CainBotClient(intents=intents)
    client.run(client.discord_token)


def setup_config():
    with open('cainbot.conf') as json_file:
        return json.load(json_file)


def all_zones_flat():
    return [zone for act_zones in all_zones for zone in act_zones]


class Notify(enum.Enum):
    OFF = "off"
    MENTION = "mention"
    DM = "dm"
    BOTH = "both"

    @property
    def is_mention(self):
        return self == Notify.MENTION or self == Notify.BOTH

    @property
    def is_dm(self):
        return self == Notify.DM or self == Notify.BOTH


class CainBotClient(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, command_prefix=('!', '.'))

        self.config = setup_config()
        self.current_terror_zone = None
        self.tracking = CainBotClient.read_tracking()
        self.rune_tracker = RuneTracker(self) if self.config.get("track_runes", False) else None
        self.d2runewizard_client = D2RunewizardClient(contact_email=self.config["contact_email"])

    @property
    def discord_token(self):
        return self.config["discord_token"]

    async def send_event(self, message: str):
        channel_name = self.config["discord_channel_name"]
        channels = [channel for channel in self.get_all_channels() if channel.name == channel_name]
        if not channels:
            print('ERROR: Unable to access channel, please check discord_channel_name')
        for channel in channels:
            if isinstance(channel, discord.abc.Messageable):
                await channel.send(message)
            else:
                print(f'ERROR: channel is unsupported type: {type(channel)}')

    @staticmethod
    def read_tracking():
        try:
            with open('tracking.json') as json_file:
                return json.load(json_file)
        except IOError:
            return {"users": {}}

    def write_tracking(self):
        with open('tracking.json', 'w') as json_file:
            return json.dump(self.tracking, json_file)

    def get_or_add_user(self, user) -> dict[str, typing.Any]:
        if str(user.id) not in self.tracking["users"]:
            self.tracking["users"][str(user.id)] = {
                "track_list": [],
                "notify": Notify.MENTION.value,
                "name": str(user)
            }
        return self.tracking["users"][str(user.id)]

    def try_get_user(self, user) -> typing.Optional[dict[str, typing.Any]]:
        return self.tracking["users"].get(str(user.id))

    def get_rune_emoji(self, ctx: commands.Context, rune):
        rune = rune.lower()
        if ctx.guild:
            # Use emoji in current server, if this isn't a DM
            for emoji in ctx.guild.emojis:
                if emoji.name == rune:
                    return str(emoji)
        # Fall back to an emoji from any server this bot is a member of
        for emoji in ctx.bot.emojis:
            if emoji.name == rune:
                return str(emoji)

        # Oh no, just print rune name with capital letter
        return rune.title()

    async def on_ready(self):
        print(f'Bot logged into Discord as "{self.user}"')
        servers = sorted([g.name for g in self.guilds])
        print(f'Connected to {len(servers)} servers: {", ".join(servers)}')

        general_cog = GeneralCog(self)
        if self.help_command is not None:
            self.help_command.cog = general_cog
        await self.add_cog(general_cog)
        await self.add_cog(TerrorZoneCog(self))
        if self.rune_tracker is not None:
            await self.add_cog(RuneDropCog(self))

        try:
            await self.wait_until_ready()
            await self.check_terror_zone()
            self.check_terror_zone_task.start()
        except RuntimeError as err:
            print(f'Background Task Error: {err}')
        await self.send_event("I'm back online, stay awhile and listen!\nType `.help` for more info.")

    async def on_command_error(self, context, exception):
        await context.send(str(exception))
        return await super().on_command_error(context, exception)

    @tasks.loop(time=POLL_TIMES)
    async def check_terror_zone_task(self):
        await self.check_terror_zone()

    async def check_terror_zone(self):
        zone = self.d2runewizard_client.get_terror_zone()
        zone_name = zone.name if zone else None
        await self.set_tzone(zone_name)

    async def set_tzone(self, zone_name):
        if self.current_terror_zone != zone_name and zone_name is not None:
            tracking_users = []
            for user_id, userdata in self.tracking["users"].items():
                notify_mode = Notify(userdata["notify"])
                is_tracked_zone = zone_name in userdata["track_list"]
                if is_tracked_zone and notify_mode.is_mention:
                    tracking_users.append(user_id)
                if is_tracked_zone and notify_mode.is_dm:
                    user = await self.fetch_user(user_id)
                    print(f'Sending new tracked zone to user_id: {user_id}, user(): {user}')
                    await user.send(f'Terror zone changed to tracked **{zone_name}**!')
            lines = []
            lines.append(f'Terror zone changed! Old zone was {self.current_terror_zone}')
            if tracking_users:
                lines.append("Ping " + " ".join([f"<@{user}>" for user in tracking_users]))
            lines.append(f'New terror zone is **{zone_name}**')
            await self.send_event('\n'.join(lines))
            self.current_terror_zone = zone_name


class RuneTracker():
    def __init__(self, bot_client):
        self.bot_client = typing.cast(CainBotClient, bot_client)

    @staticmethod
    def parse_rune(name: str) -> str:
        rune = name.strip(':').lower()
        if rune not in runes:
            raise Exception(f'No such rune \"{rune}\"')
        return rune

    def add(self, discord_user, rune_str: str, date: datetime.date):
        user = self.bot_client.get_or_add_user(discord_user)
        rune = self.parse_rune(rune_str)
        user.setdefault("runedrop_list", []).append({'rune': rune, 'date': date.isoformat()})
        self.bot_client.write_tracking()
        return rune, date

    def list_for(self, discord_user):
        user = self.bot_client.try_get_user(discord_user)
        if user is None:
            return None
        return user.get("runedrop_list")

    def top(self, n: int):
        def sort_key(rune_drop):
            return runes.index(rune_drop['rune'])
        return sorted(self._all_rune_drops(), key=sort_key, reverse=True)[:n]

    def pb(self):
        user_rune_drops: dict[str, typing.Any] = {}
        for rune_drop in self._all_rune_drops():
            current_user = rune_drop['user']
            if current_user in user_rune_drops:
                current_user_best_drop = user_rune_drops[current_user]
                if runes.index(current_user_best_drop['rune']) < runes.index(rune_drop['rune']):
                    user_rune_drops[current_user] = rune_drop
            else:
                user_rune_drops[current_user] = rune_drop
        return [dict(v, user=k) for k, v in user_rune_drops.items()]

    def _all_rune_drops(self) -> list[dict[str, typing.Any]]:
        rune_drops = []
        for user_id, userdata in self.bot_client.tracking["users"].items():
            for rune_drop in userdata.get("runedrop_list", []):
                rune_drops.append(dict(rune_drop, user=userdata["name"]))
        return rune_drops


class GeneralCog(commands.Cog, name="General"):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def gdpr(self, ctx):
        """
        Get all stored data on your user.
        """
        user = self.client.try_get_user(ctx.author)
        if user is not None:
            await ctx.send(f'Data on {ctx.author}:\n```{user}```')
        else:
            await ctx.send(f'{ctx.author} not stored')

    @commands.command(name="forget-me")
    async def forget_me(self, ctx):
        """
        Delete all stored data on your user.
        """
        if str(ctx.author.id) in self.client.tracking["users"]:
            del self.client.tracking["users"][str(ctx.author.id)]
            self.client.write_tracking()
            await ctx.send(f'Data on {ctx.author} removed')
        else:
            await ctx.send(f'{ctx.author} not stored')


class TerrorZoneCog(commands.Cog, name="Terror zones"):
    def __init__(self, client):
        self.client = client

    @commands.command()
    async def tzone(self, ctx):
        """
        Show current active terror zone.
        """
        print(f'Responding to tzone chatop from {ctx.author}')
        zone = self.client.current_terror_zone
        response = zone if zone else "Unknown zone"
        await ctx.send(response)

    @commands.command(name="list-zones")
    async def list_zones(self, ctx):
        """
        List all available terror zones.
        """
        print(f'Responding to list-zones chatop from {ctx.author}')
        user = self.client.try_get_user(ctx.author)
        formatted_zones = ""
        for act, zones in enumerate(all_zones):
            formatted_zones += f"Act {act+1}:\n"
            for zone in zones:
                if user is not None and zone in user["track_list"]:
                    formatted_zones += f"  * {zone}\n"
                else:
                    formatted_zones += f"    {zone}\n"
        await ctx.send(f'Available zones (asterisk before tracked ones):\n```{formatted_zones}```')

    @commands.command(name="set-tzone")
    async def set_tzone(self, ctx, zone_name):
        """
        Update current active terror zone.
        """
        print(f'Responding to set-tzone chatop from {ctx.author}')
        if zone_name not in all_zones_flat():
            return await ctx.send(f"Unknown zone: {zone_name}")
        await self.client.set_tzone(zone_name)

    @commands.command()
    async def track(self, ctx, zone_name=commands.parameter(
            description='The whole name of the zone(s) to track, see `.list-zones`.')):
        """
        Track specific terror zone, bot will ping you.
        """
        print(f'Responding to track chatop from {ctx.author}')
        if zone_name not in all_zones_flat():
            await ctx.send(f'Unknown zone: `{zone_name}`')
            return
        user = self.client.get_or_add_user(ctx.author)
        if zone_name in user["track_list"]:
            await ctx.send(f'{ctx.author} already tracking {zone_name}')
        else:
            user["track_list"].append(zone_name)
            self.client.write_tracking()
            await ctx.send(f'{ctx.author} now tracking {zone_name}')

    @commands.command()
    async def untrack(self, ctx, zone_name):
        """
        Remove tracking.
        """
        print(f'Responding to untrack chatop from {ctx.author}')
        user = self.client.try_get_user(ctx.author)
        if not user:
            await ctx.send(f'{ctx.author} has no tracking data stored')
            return

        if zone_name in user["track_list"]:
            user["track_list"].remove(zone_name)
            self.client.write_tracking()
            await ctx.send(f'{ctx.author} no longer tracking {zone_name}')
        else:
            await ctx.send(f'{ctx.author} did not track {zone_name}')

    @commands.command()
    async def notify(self, ctx, mode: typing.Literal[None, "off", "mention", "dm", "both"] = None):
        """
        Set notification mode (off=no notifications, mention=ping in events channel, dm=private message,
        both=mention and dm).
        """
        print(f'Responding to notify chatop from {ctx.author}, mode: {mode}')
        user = self.client.get_or_add_user(ctx.author)
        if mode is not None:
            user["notify"] = mode
            self.client.write_tracking()
        await ctx.send(f'{ctx.author} notification mode set to "{user["notify"]}"')


class RuneDropCog(commands.Cog, name="Rune drops"):
    def __init__(self, client: CainBotClient):
        self.client = client

    @property
    def rune_tracker(self) -> RuneTracker:
        return typing.cast(RuneTracker, self.client.rune_tracker)

    @commands.command(name="runedrop-add")
    async def runedrop_add(self, ctx: commands.Context, rune: str, date: typing.Optional[str] = None):
        """
        Add rune drop to personal list.
        """
        if date is None:
            date = datetime.date.today().isoformat()
        date_obj = datetime.date.fromisoformat(date)
        print(f'Responding to runedrop-add chatop from {ctx.author}, rune: {rune}, date: {date_obj}')
        added_rune, added_date = self.rune_tracker.add(ctx.author, rune, date_obj)
        await ctx.send(f'{ctx.author} added :{added_rune}: on {added_date}')

    @commands.command(name="runedrop-list")
    async def runedrop_list(self, ctx: commands.Context):
        """
        List all personal rune drops.
        """
        print(f'Responding to runedrop-list chatop from {ctx.author}')
        runes = self.rune_tracker.list_for(ctx.author)
        if not runes:
            return await ctx.send(f'{ctx.author} has no tracked rune drops in current season')
        rune_list_str = self._build_rune_list_str(ctx, runes)
        await ctx.send(f'{ctx.author} rune drops in current season:\n{rune_list_str}')

    @commands.command(name="runedrop-top")
    async def runedrop_top(self, ctx: commands.Context, n: int = 5):
        """
        List top `n` highest registered rune drops among all players.
        """
        print(f'Responding to runedrop-pb chatop from {ctx.author}')
        runes = self.rune_tracker.top(n)
        if not runes:
            return await ctx.send('There are no tracked rune drops in current season')
        rune_list_str = self._build_rune_list_str(ctx, runes)
        await ctx.send(f'Highest rune drops in current season among all players:\n{rune_list_str}')

    @commands.command(name="runedrop-pb")
    async def runedrop_pb(self, ctx: commands.Context):
        """
        List each player's personal best (highest rune drop).
        """
        print(f'Responding to runedrop-pb chatop from {ctx.author}')
        runes = self.rune_tracker.pb()
        if not runes:
            return await ctx.send('There are no tracked rune drops in current season')
        rune_list_str = self._build_rune_list_str(ctx, runes)
        await ctx.send(f"Each player's best rune drop in current season:\n{rune_list_str}")

    def _build_rune_list_str(self, ctx: commands.Context, runes: list[dict[str, typing.Any]]):
        rune_list_str = ''
        for rune in runes:
            date_obj = datetime.date.fromisoformat(rune["date"])
            rune_emoji = self.client.get_rune_emoji(ctx, rune["rune"])
            timestamp = int(time.mktime(date_obj.timetuple()))
            user_prefix = rune['user']+' ' if 'user' in rune else ''
            rune_list_str += f'* {user_prefix}{rune_emoji} (<t:{timestamp}:d>)\n'
        return rune_list_str


if __name__ == "__main__":
    main()
