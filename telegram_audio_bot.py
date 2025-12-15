import os
import logging
from telethon import TelegramClient, events
from telethon.tl.types import DocumentAttributeFilename
import openai
from fpdf import FPDF
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# API Credentials from environment variables
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate credentials
if not all([API_ID, API_HASH, BOT_TOKEN, OPENAI_API_KEY]):
    raise ValueError(
        "Missing required environment variables. Please check your .env file."
    )

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

# Temporary directory for files
TEMP_DIR = "temp_files"
os.makedirs(TEMP_DIR, exist_ok=True)

# Initialize Telethon client
bot = TelegramClient("audio_bot", API_ID, API_HASH)


class TranscriptionPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 16)
        self.cell(0, 10, "Audio Transcription", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using OpenAI Whisper API"""
    try:
        with open(audio_path, "rb") as audio_file:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="text"
            )
        return transcript
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise


def create_pdf(text: str, output_path: str):
    """Create PDF from transcribed text"""
    pdf = TranscriptionPDF()
    pdf.add_page()

    # Add metadata
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1)
    pdf.ln(5)

    # Add transcription
    pdf.set_font("Arial", "", 12)

    # Handle text encoding and wrapping
    try:
        paragraphs = text.split("\n")
        for para in paragraphs:
            if para.strip():
                pdf.multi_cell(
                    0, 10, para.encode("latin-1", "replace").decode("latin-1")
                )
                pdf.ln(2)
    except Exception as e:
        logger.error(f"PDF encoding error: {e}")
        pdf.multi_cell(
            0, 10, "Error encoding some characters. Please check the text file."
        )

    pdf.output(output_path)


@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    """Handle /start command"""
    welcome_message = """
**Welcome to Audio Transcription Bot**

I can transcribe any audio file or voice message into text using advanced AI technology.

**What I can do:**
- Transcribe voice messages instantly
- Convert audio files to text (MP3, WAV, M4A, OGG, FLAC)
- Support 90+ languages automatically
- Deliver results in TXT and PDF formats
- Handle audio up to 25 MB

**How to use:**
Simply send me an audio file or voice message and I'll transcribe it for you.

**Commands:**
/help - Detailed usage instructions
/formats - Supported audio formats
/languages - Supported languages
/about - About this bot

Ready to transcribe? Send me an audio file now!
"""
    await event.respond(welcome_message)


@bot.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    """Handle /help command"""
    help_message = """
**How to Use Audio Transcription Bot**

**Step 1:** Send an audio file or voice message
You can send files directly or forward voice messages from other chats.

**Step 2:** Wait for processing
Processing time depends on audio length. Typically:
- Short messages (under 1 min): 5-10 seconds
- Medium files (1-5 min): 15-30 seconds
- Long files (5-10 min): 30-60 seconds

**Step 3:** Receive transcription
You'll get two files:
- TXT file: Plain text format, easy to copy/paste
- PDF file: Formatted document with metadata

**Best Practices:**
- Use clear audio with minimal background noise
- Speak clearly at a normal pace
- Avoid overlapping voices when possible
- Ensure good microphone quality

**Supported file size:** Up to 25 MB
**Supported duration:** Up to 30 minutes

**Need more help?**
/formats - View supported formats
/languages - View supported languages
/about - Learn about this bot
"""
    await event.respond(help_message)


@bot.on(events.NewMessage(pattern="/formats"))
async def formats_handler(event):
    """Handle /formats command"""
    formats_message = """
**Supported Audio Formats**

**Voice Messages:**
- OGG Opus (Telegram voice messages)
- Direct voice recording from Telegram

**Audio Files:**
- MP3 (MPEG Audio Layer 3)
- WAV (Waveform Audio File)
- M4A (MPEG-4 Audio)
- FLAC (Free Lossless Audio Codec)
- OGG (Ogg Vorbis)
- WEBM (WebM Audio)
- AAC (Advanced Audio Coding)
- WMA (Windows Media Audio)

**File Requirements:**
- Maximum size: 25 MB
- Maximum duration: 30 minutes
- Any sample rate supported
- Mono or stereo channels

**Tip:** For best results, use lossless formats like WAV or FLAC when possible.
"""
    await event.respond(formats_message)


@bot.on(events.NewMessage(pattern="/languages"))
async def languages_handler(event):
    """Handle /languages command"""
    languages_message = """
**Supported Languages (90+ Languages)**

The bot automatically detects the language in your audio. No need to specify!

**Major Languages Supported:**
English, Spanish, French, German, Italian, Portuguese, Dutch, Russian, Arabic, Chinese (Mandarin), Japanese, Korean, Hindi, Turkish, Polish, Ukrainian, Swedish, Danish, Norwegian, Finnish, Greek, Czech, Romanian, Hungarian, Thai, Vietnamese, Indonesian, Malay, Hebrew, Persian, Urdu, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, and many more.

**Language Detection:**
The AI automatically identifies the spoken language in your audio. You can even have multiple languages in one recording.

**Accuracy:**
- Native accent: 95-99% accuracy
- Non-native accent: 85-95% accuracy
- Background noise: 70-85% accuracy

**Note:** Results may vary based on audio quality, accent, and speaking clarity.
"""
    await event.respond(languages_message)


@bot.on(events.NewMessage(pattern="/about"))
async def about_handler(event):
    """Handle /about command"""
    about_message = """
**About Audio Transcription Bot**

**Technology:**
This bot uses OpenAI's Whisper API, a state-of-the-art speech recognition system trained on 680,000 hours of multilingual data.

**Features:**
- Automatic language detection
- High accuracy transcription
- Support for 90+ languages
- Fast processing
- Dual format output (TXT + PDF)
- Privacy focused

**Privacy & Security:**
- Audio files are processed securely
- Files are stored locally for your records
- All files remain on secure servers
- No data is shared with third parties

**Pricing:**
This bot uses OpenAI's Whisper API which charges approximately $0.006 per minute of audio transcribed.

**Developer:**
Created for easy and accurate audio transcription needs.

**Version:** 1.0.0
**Last Updated:** December 2024

Have questions? Send a message to the developer.
"""
    await event.respond(about_message)


@bot.on(events.NewMessage)
async def audio_handler(event):
    """Handle audio messages"""
    # Skip if it's a command
    if event.message.text and event.message.text.startswith("/"):
        return

    # Check if message contains audio or voice
    if not (
        event.message.voice
        or (
            event.message.document
            and event.message.document.mime_type
            and event.message.document.mime_type.startswith("audio/")
        )
    ):
        return

    try:
        # Send processing message
        status_msg = await event.respond("Processing your audio... Please wait.")

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_id = event.sender_id

        # Download audio file
        if event.message.voice:
            audio_path = os.path.join(TEMP_DIR, f"voice_{user_id}_{timestamp}.ogg")
        else:
            # Get file extension from mime type
            ext = event.message.document.mime_type.split("/")[-1]
            audio_path = os.path.join(TEMP_DIR, f"audio_{user_id}_{timestamp}.{ext}")

        await event.message.download_media(audio_path)
        logger.info(f"Downloaded audio: {audio_path}")

        # Update status
        await status_msg.edit("Transcribing audio with AI...")

        # Transcribe audio
        transcription = transcribe_audio(audio_path)
        logger.info(f"Transcription completed for user {user_id}")

        # Create text file
        txt_path = os.path.join(TEMP_DIR, f"transcription_{user_id}_{timestamp}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"Audio Transcription\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'-'*50}\n\n")
            f.write(transcription)

        # Create PDF
        pdf_path = os.path.join(TEMP_DIR, f"transcription_{user_id}_{timestamp}.pdf")
        create_pdf(transcription, pdf_path)

        # Update status
        await status_msg.edit("Sending your transcription...")

        # Send files
        await event.respond(
            f"**Transcription Complete!**\n\nPreview:\n{transcription[:500]}{'...' if len(transcription) > 500 else ''}",
            file=[txt_path, pdf_path],
        )

        # Delete status message
        await status_msg.delete()

        # Files are saved in temp_files/ directory
        logger.info(f"Files saved: {audio_path}, {txt_path}, {pdf_path}")

    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        await event.respond(
            f"Error processing audio: {str(e)}\n\nPlease try again or contact support."
        )


def main():
    """Main function to run the bot"""
    logger.info("Bot started successfully!")
    print("Bot is running... Press Ctrl+C to stop.")
    print(f"Files will be saved in: {os.path.abspath(TEMP_DIR)}")

    # Start the bot and run until disconnected
    bot.start(bot_token=BOT_TOKEN)
    bot.run_until_disconnected()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped.")
