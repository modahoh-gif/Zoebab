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

# المتغيرات الأساسية
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))
COOKIES_CONTENT = os.getenv("YT_COOKIES")

async def download_audio_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    status_msg = await update.message.reply_text("⏳ Processing... Using Docker environment.")
    
    unique_id = str(update.message.message_id)
    filename = f"audio_{unique_id}"
    cookie_path = f"cookies_{unique_id}.txt"

    try:
        # إنشاء ملف الكوكيز
        if COOKIES_CONTENT:
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write(COOKIES_CONTENT.strip())
                f.write("\n")

        # إعدادات متينة جداً لتجنب خطأ Requested Format
        ydl_opts = {
            # نطلب أفضل جودة متاحة (فيديو أو صوت) لضمان عدم حدوث خطأ التوفر
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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            },
        }

        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await asyncio.to_thread(run_dl)
        
        expected_file = f"{filename}.mp3"
        
        if os.path.exists(expected_file):
            await status_msg.edit_text("✅ Downloaded via Docker! Sending...")
            with open(expected_file, "rb") as audio:
                await update.message.reply_audio(audio=audio)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Error: Audio extraction failed. FFmpeg might be missing in Docker.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)[:150]}")
    
    finally:
        # تنظيف الملفات
        if os.path.exists(cookie_path): os.remove(cookie_path)
        for ext in ['mp3', 'webm', 'm4a', 'mp4', 'ytdl', 'part']:
            f = f"{filename}.{ext}"
            if os.path.exists(f): os.remove(f)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        asyncio.create_task(download_audio_task(update, context))
    else:
        await update.message.reply_text("Please send a valid YouTube link.")

def main():
    if not TOKEN or not WEBHOOK_URL:
        print("Set BOT_TOKEN and WEBHOOK_URL!")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"Bot starting on port {PORT}...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
