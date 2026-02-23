import asyncio
import os
import yt_dlp
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

# Configuration from Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))
COOKIES_CONTENT = os.getenv("YT_COOKIES")

async def download_audio_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Background task to handle downloading and converting audio"""
    url = update.message.text
    status_msg = await update.message.reply_text("⏳ Processing your request... Please wait.")
    
    unique_id = str(update.message.message_id)
    filename = f"audio_{unique_id}"
    cookie_path = f"cookies_{unique_id}.txt"

    try:
        # 1. Write cookies to a temporary file with clean formatting
        if COOKIES_CONTENT:
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write(COOKIES_CONTENT.strip())
                f.write("\n")

        # 2. Optimized yt-dlp options to avoid 'Format Not Available'
        ydl_opts = {
            # Use 'bestaudio' and let FFmpeg handle the conversion to MP3
            "format": "bestaudio/best",
            "outtmpl": f"{filename}.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "cookiefile": cookie_path if COOKIES_CONTENT else None,
            "nocheckcertificate": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            }
        }

        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        # Run the blocking download in a separate thread
        await asyncio.to_thread(run_dl)
        
        expected_file = f"{filename}.mp3"
        
        if os.path.exists(expected_file):
            await status_msg.edit_text("✅ Download complete! Sending to Telegram...")
            with open(expected_file, "rb") as audio:
                await update.message.reply_audio(
                    audio=audio,
                    caption=f"🎵 Successfully Downloaded\n🔗 {url}"
                )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Error: Audio file not found. Check if FFmpeg is installed.")

    except Exception as e:
        error_msg = str(e)
        print(f"Error details: {error_msg}")
        await status_msg.edit_text(f"❌ Failed: {error_msg[:100]}")
    
    finally:
        # Cleanup temporary files
        if os.path.exists(cookie_path): os.remove(cookie_path)
        if os.path.exists(f"{filename}.mp3"): os.remove(f"{filename}.mp3")
        # Cleanup any stray files from failed downloads
        for ext in ['webm', 'm4a', 'ytdl', 'part']:
            temp_file = f"{filename}.{ext}"
            if os.path.exists(temp_file): os.remove(temp_file)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point for text messages to avoid Webhook timeout"""
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        # Launch the task without blocking the response to Telegram
        asyncio.create_task(download_audio_task(update, context))
    else:
        await update.message.reply_text("❌ Please send a valid YouTube link.")

def main():
    if not TOKEN or not WEBHOOK_URL:
        print("Set BOT_TOKEN and WEBHOOK_URL in environment variables.")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"Starting bot on port {PORT}...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
