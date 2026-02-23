import os
import yt_dlp
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://your-app.onrender.com

app = Flask(__name__)
bot = Bot(token=TOKEN)

telegram_app = ApplicationBuilder().token(TOKEN).build()

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("أرسل رابط يوتيوب صحيح")
        return

    await update.message.reply_text("جاري التحميل...")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    await update.message.reply_audio(audio=open("audio.mp3", "rb"))
    os.remove("audio.mp3")

telegram_app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, download_audio)
)

@app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)
    await telegram_app.process_update(update)
    return "ok"

@app.route("/")
def home():
    return "Bot is running!"

if __name__ == "__main__":
    import asyncio
    asyncio.run(bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}"))
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
