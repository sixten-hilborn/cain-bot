# This example requires the 'message_content' intent.

import discord
import json
import requests
import typing
import enum
from discord.ext import tasks
from discord.ext import commands

__version__ = '0.1.0'
client = None

act1_zones = [
    "Blood Moor and Den of Evil",
    "Cold Plains and The Cave",
    "Burial Grounds, The Crypt, and The Mausoleum",
    "Stony Field",
    "Dark Wood",
    "The Forgotten Tower",
    "Jail",
    "Cathedral and Catacombs",
    "The Pit",
]
act2_zones = [
    "Sewers",
    "Rocky Waste and Stony Tomb",
    "Dry Hills and Halls of the Dead",
    "Far Oasis",
    "Lost City, Valley of Snakes, and Claw Viper Temple",
    "Arcane Sanctuary",
    "Tal Rasha's Tombs and Tal Rasha's Chamber",
]
act3_zones = [
    "Spider Forest and Spider Cavern",
    "Flayer Jungle and Flayer Dungeon",
    "Kurast Bazaar, Ruined Temple, and Disused Fane",
    "Kurast Sewers",
    "Travincal",
    "Durance of Hate",
]
act4_zones = [
    "Outer Steppes and Plains of Despair",
    "River of Flame and City of the Damned",
    "Chaos Sanctuary",
]
act5_zones = [
    "Bloody Foothills",
    "Frigid Highlands",
    "Glacial Trail",
    "Crystalline Passage and Frozen River",
    "Arreat Plateau",
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

def main():
    global client
    intents = discord.Intents.default()
    intents.message_content = True

    client = CainBotClient(intents=intents)
    client.run(client.discord_token)

def setup_config():
    with open('cainbot.conf') as json_file:
        return json.load(json_file)


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

        self.add_command(tzone)
        self.add_command(list_zones)
        self.add_command(track)
        self.add_command(untrack)
        self.add_command(gdpr)
        self.add_command(forget_me)
        self.add_command(notify)

    @property
    def discord_token(self):
        return self.config["discord_token"]

    async def send_event(self, message):
        channels = [channel for channel in self.get_all_channels() if channel.name == self.config["discord_channel_name"]]
        if not channels:
            print('ERROR: Unable to access channel, please check discord_channel_name')
        for channel in channels:
            await channel.send(message)

    @staticmethod
    def read_tracking():
        try:
            with open('tracking.json') as json_file:
                return json.load(json_file)
        except IOError:
            return {"users":{}}

    def write_tracking(self):
        with open('tracking.json', 'w') as json_file:
            return json.dump(self.tracking, json_file)

    def get_or_add_user(self, user):
        if str(user.id) not in self.tracking["users"]:
            self.tracking["users"][str(user.id)] = {"track_list":[], "notify":Notify.MENTION.value, "name":str(user)}
        return self.tracking["users"][str(user.id)]

    async def on_ready(self):
        print(f'Bot logged into Discord as "{self.user}"')
        servers = sorted([g.name for g in self.guilds])
        print(f'Connected to {len(servers)} servers: {", ".join(servers)}')

        try:
            await self.wait_until_ready()
            self.check_terror_zone.start()
        except RuntimeError as err:
            print(f'Background Task Error: {err}')
        await self.send_event("I'm back online, stay awhile and listen!\nType `.help` for more info.")

    async def on_command_error(self, context, exception):
        await context.send(str(exception))
        return await super().on_command_error(context, exception)


    @tasks.loop(seconds=60)
    async def check_terror_zone(self):
        zone = D2RunewizardClient.get_terror_zone()
        zone_name = zone["terrorZone"]["zone"]
        if self.current_terror_zone != zone_name:
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
            message = "" if not tracking_users else "Ping " + " ".join([f"<@{user}>" for user in tracking_users]) + "\n"
            await self.send_event(f'Terror zone changed! Old zone was {self.current_terror_zone}\n{message}New terror zone is **{zone_name}**')
            self.current_terror_zone = zone_name

@commands.command()
async def tzone(ctx):
    """
    Show current active terror zone.
    """
    print(f'Responding to tzone chatop from {ctx.author}')
    zone = client.current_terror_zone
    response = zone if zone else "Unknown zone"
    await ctx.send(response)

@commands.command(name="list-zones")
async def list_zones(ctx):
    """
    List all available terror zones.
    """
    print(f'Responding to list-zones chatop from {ctx.author}')
    formatted_zones = ""
    for act, zones in enumerate(all_zones):
        formatted_zones += f"Act {act+1}:\n"
        for zone in zones:
            formatted_zones += f"    {zone}\n"
    await ctx.send(f'Available zones:\n```{formatted_zones}```')

@commands.command()
async def track(ctx, zone_name):
    """
    Track specific terror zone, bot will ping you.
    """
    print(f'Responding to track chatop from {ctx.author}')
    all_zones_flat = [zone for act_zones in all_zones for zone in act_zones]
    if zone_name not in all_zones_flat:
        await ctx.send(f'Unknown zone: `{zone_name}`')
        return
    user = client.get_or_add_user(ctx.author)
    if zone_name in user["track_list"]:
        await ctx.send(f'{ctx.author} already tracking {zone_name}')
    else:
        user["track_list"].append(zone_name)
        client.write_tracking()
        await ctx.send(f'{ctx.author} now tracking {zone_name}')

@commands.command()
async def untrack(ctx, zone_name):
    """
    Remove tracking.
    """
    print(f'Responding to untrack chatop from {ctx.author}')
    user = client.tracking["users"].get(str(ctx.author.id))
    if not user:
        await ctx.send(f'{ctx.author} has no tracking data stored')
        return

    if zone_name in user["track_list"]:
        user["track_list"].remove(zone_name)
        client.write_tracking()
        await ctx.send(f'{ctx.author} no longer tracking {zone_name}')
    else:
        await ctx.send(f'{ctx.author} did not track {zone_name}')

@commands.command()
async def gdpr(ctx):
    """
    Get all stored data on your user.
    """
    if str(ctx.author.id) in client.tracking["users"]:
        await ctx.send(f'Data on {ctx.author}:\n```{client.tracking["users"][str(ctx.author.id)]}```')
    else:
        await ctx.send(f'{ctx.author} not stored')

@commands.command(name="forget-me")
async def forget_me(ctx):
    """
    Delete all stored data on your user.
    """
    if str(ctx.author.id) in client.tracking["users"]:
        del client.tracking["users"][str(ctx.author.id)]
        client.write_tracking()
        await ctx.send(f'Data on {ctx.author} removed')
    else:
        await ctx.send(f'{ctx.author} not stored')

@commands.command()
async def notify(ctx, mode: typing.Literal[None, "off", "mention", "dm", "both"] = None):
    """
    Set notification mode (off=no notifications, mention=ping in events channel, dm=private message, both=mention and dm).
    """
    print(f'Responding to notify chatop from {ctx.author}, mode: {mode}')
    user = client.get_or_add_user(ctx.author)
    if not mode is None:
        user["notify"] = mode
        client.write_tracking()
    await ctx.send(f'{ctx.author} notification mode set to "{user["notify"]}"')

class D2RunewizardClient():
    @staticmethod
    def get_terror_zone():
        try:
            response = requests.get(f'https://d2runewizard.com/api/terror-zone', params=D2RunewizardClient.get_api_token_params(), timeout=10)
            response.raise_for_status()

            return response.json()
        except Exception as err:
            print(f'[TerrorZone] D2Runewizard API Error: {err}')
            return None

    @staticmethod
    def get_api_token_params():
        payload = {}
        return payload



if __name__ == "__main__":
    main()
