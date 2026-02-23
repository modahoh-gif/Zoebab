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

# Environment Variables
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))
# This is the variable where you will paste the cookies text
COOKIES_CONTENT = os.getenv("YT_COOKIES")

async def download_audio_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    status_msg = await update.message.reply_text("⏳ Processing your request... please wait.")
    
    unique_id = str(update.message.message_id)
    filename = f"audio_{unique_id}"
    cookie_path = f"cookies_{unique_id}.txt"

    # Create temporary cookie file if content exists
    if COOKIES_CONTENT:
        with open(cookie_path, "w") as f:
            f.write(COOKIES_CONTENT)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{filename}.%(ext)s",
        "quiet": True,
        "cookiefile": cookie_path if COOKIES_CONTENT else None,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await asyncio.to_thread(run_dl)
        
        expected_file = f"{filename}.mp3"
        if os.path.exists(expected_file):
            await status_msg.edit_text("✅ Download complete! Uploading...")
            with open(expected_file, "rb") as audio:
                await update.message.reply_audio(
                    audio=audio, 
                    caption=f"🎵 Downloaded Successfully\n🔗 {url}"
                )
            os.remove(expected_file)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Conversion error. Make sure FFmpeg is installed.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)[:100]}")
    
    finally:
        # Cleanup
        if os.path.exists(expected_file): os.remove(expected_file)
        if os.path.exists(cookie_path): os.remove(cookie_path)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        # Run the heavy task in background to avoid Webhook timeout
        asyncio.create_task(download_audio_task(update, context))
    else:
        await update.message.reply_text("Please send a valid YouTube link.")

def main():
    if not TOKEN or not WEBHOOK_URL:
        print("Set BOT_TOKEN and WEBHOOK_URL in Render settings!")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"Server starting on port {PORT}...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
