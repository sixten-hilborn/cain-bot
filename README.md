# cain-bot

Discord bot for Diablo 2 Resurrected events.

## Features

* Terror zone tracker
* Friendly rune drop high-score

## Setup

First install Python dependencies:

```bash
pip install -r requirements.txt
```

Then [create a Discord app and bot](https://discord.com/developers/docs/getting-started#creating-an-app).

Then create `cainbot.conf` with your Discord token

```json
{
    "contact_email": "<your email goes here>",
    "discord_token": "<your discord token goes here>",
    "discord_channel_name": "events"
}
```

Finally start the bot with:

```bash
python -m cainbot
```

## Development

Run unit tests with:

```bash
python -m unittest
```
