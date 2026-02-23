import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

async def download_audio_task(update: Update, url: str):
    """تشغيل التحميل في Thread بدون تعليق البوت"""
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{update.message.message_id}.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
    }

    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    await asyncio.to_thread(download)

    audio_file = f"{update.message.message_id}.mp3"
    await update.message.reply_audio(audio=open(audio_file, "rb"))
    os.remove(audio_file)


async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("أرسل رابط يوتيوب صحيح")
        return

    # الرد الفوري
    await update.message.reply_text("جاري التحميل... 🚀")

    # تشغيل التحميل في background task
    asyncio.create_task(download_audio_task(update, url))


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
        url_path=TOKEN,
    )


if __name__ == "__main__":
    main()
