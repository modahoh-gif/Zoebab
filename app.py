import os
import yt_dlp
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-app.onrender.com

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("أرسل رابط يوتيوب صحيح")
        return

    await update.message.reply_text("جاري التحميل...")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "audio.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    await update.message.reply_audio(audio=open("audio.mp3", "rb"))
    os.remove("audio.mp3")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
    )

if __name__ == "__main__":
    main()
