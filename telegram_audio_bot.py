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
**Audio Transcription Bot**

Welcome! Send me any audio file and I'll transcribe it for you.

**Supported formats:**
- Voice messages
- Audio files (MP3, OGG, WAV, M4A, etc.)

**You'll receive:**
- Text file (.txt)
- PDF document (.pdf)

Just send an audio file to get started!
"""
    await event.respond(welcome_message)


@bot.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    """Handle /help command"""
    help_message = """
**How to use:**

1. Send me a voice message or audio file
2. Wait while I transcribe it (this may take a moment)
3. Receive your transcription in both TXT and PDF formats

**Tips:**
- Clear audio works best
- Supported languages: 90+ languages via Whisper AI
- Max file size: ~25 MB

Need help? Contact the developer.
"""
    await event.respond(help_message)


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

        # Cleanup files
        os.remove(audio_path)
        os.remove(txt_path)
        os.remove(pdf_path)
        logger.info(f"Cleaned up files for user {user_id}")

    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        await event.respond(
            f"Error processing audio: {str(e)}\n\nPlease try again or contact support."
        )


def main():
    """Main function to run the bot"""
    logger.info("Bot started successfully!")
    print("Bot is running... Press Ctrl+C to stop.")

    # Start the bot and run until disconnected
    bot.start(bot_token=BOT_TOKEN)
    bot.run_until_disconnected()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBot stopped.")
