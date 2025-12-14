# Telegram Audio Transcription Bot

A simple Telegram bot that transcribes audio files using OpenAI Whisper API.

## Setup

1. Install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Create `.env` file with your credentials:
```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
OPENAI_API_KEY=your_openai_key
```

3. Get credentials:
- API_ID & API_HASH: https://my.telegram.org
- BOT_TOKEN: @BotFather on Telegram
- OPENAI_API_KEY: https://platform.openai.com/api-keys

4. Run the bot:
```bash
python3 telegram_audio_bot.py
```

## Usage

Send audio files or voice messages to the bot. You'll receive:
- Text file (.txt)
- PDF document (.pdf)

Supports 90+ languages.

## Files

- `telegram_audio_bot.py` - Main bot code
- `requirements.txt` - Dependencies
- `.env` - API credentials (create this)
- `temp_files/` - Temporary storage (auto-created)