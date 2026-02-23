import os
import yt_dlp
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://zoebab.onrender.com

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
        "quiet": True,
    }

    # تشغيل التحميل في Thread لتجنب تعليق async
    def download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    await asyncio.to_thread(download)

    await update.message.reply_audio(audio=open("audio.mp3", "rb"))
    os.remove("audio.mp3")


def main():
    # إنشاء التطبيق
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio))

    # ⚠️ المهم: url_path=TOKEN حتى يطابق Webhook مع Telegram
    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
        url_path=TOKEN,
    )


if __name__ == "__main__":
    main()
