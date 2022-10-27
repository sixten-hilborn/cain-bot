# cain-bot
Discord bot for Diablo 2 Resurrected events.

## Setup

First install Python dependencies:

```
pip3 install -r requirements.txt
```

Then [create a Discord app and bot](https://discord.com/developers/docs/getting-started#creating-an-app).

Then create `cainbot.conf` with your Discord token

```json
{
    "discord_token": "<your discord token goes here>",
    "discord_channel_name": "events"
}
```

Finally start the bot with:

```
python -m cainbot
```
