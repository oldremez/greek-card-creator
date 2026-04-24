# greek-card-creator

A personal Telegram bot that turns photos of Greek text into flashcards.

Send a photo → get back a list of normalized Greek words with Russian translations, ready to paste into Anki or any other flashcard app.

## How it works

1. You send the bot a photo (textbook page, sign, menu, exercise, etc.)
2. The bot passes the image to **Claude Opus 4.7** via the Anthropic vision API
3. Claude extracts all Greek vocabulary, normalizes each word to its dictionary form (verbs → infinitive, nouns → nominative singular, etc.), and translates to Russian
4. The bot replies with one card per line in `front::back` format

**Example output:**
```
βιβλίο::книга
τρώω::есть, кушать
καλημέρα::доброе утро
```

The `::` separator is the default Anki import format — you can paste the reply directly into a text file and import it.

## Setup

**Prerequisites:** Python 3.11+, a Telegram bot token, an Anthropic API key.

```bash
git clone https://github.com/yourname/greek-card-creator
cd greek-card-creator
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:

```
TELEGRAM_BOT_TOKEN=   # from @BotFather
ANTHROPIC_API_KEY=    # from console.anthropic.com
ALLOWED_USER_ID=      # your Telegram user ID (get it from @userinfobot)
```

Run:

```bash
python bot.py
```

## Access control

The bot silently ignores messages from anyone whose Telegram user ID does not match `ALLOWED_USER_ID`. It is designed for personal use only.

## Supported image formats

Photos sent normally (compressed by Telegram) and images sent as files — JPEG, PNG, GIF, WebP.

## Project layout

```
bot.py            — Telegram handlers
claude_client.py  — Claude API call with structured output
config.py         — env var loader
requirements.txt
.env.example
```

## Dependencies

| Package | Purpose |
|---|---|
| `python-telegram-bot` | Telegram Bot API client |
| `anthropic` | Claude API (vision + structured output) |
| `pydantic` | Response schema validation |
| `python-dotenv` | `.env` file loading |
