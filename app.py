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

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))
COOKIES_CONTENT = os.getenv("YT_COOKIES")

async def download_audio_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    status_msg = await update.message.reply_text("⏳ Searching for a compatible format...")
    
    unique_id = str(update.message.message_id)
    filename = f"audio_{unique_id}"
    cookie_path = f"cookies_{unique_id}.txt"

    try:
        # إنشاء ملف الكوكيز
        if COOKIES_CONTENT:
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write(COOKIES_CONTENT.strip())
                f.write("\n")

        # إعدادات الـ Ultra Compatibility
        ydl_opts = {
            # التغيير الجوهري هنا: نطلب أفضل فيديو مدمج (صوت وصورة) 
            # لأن يوتيوب لا يحجبها مثل ملفات الصوت المنفصلة
            "format": "best/bestvideo+bestaudio", 
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
            await status_msg.edit_text("✅ Success! Sending audio...")
            with open(expected_file, "rb") as audio:
                await update.message.reply_audio(audio=audio, caption="Done via Docker environment")
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Error: Could not extract audio. FFmpeg is required.")

    except Exception as e:
        # إذا فشل كل شيء، سنعرض الخطأ بالتفصيل لنعرف السبب
        error_detail = str(e)[:200]
        await status_msg.edit_text(f"❌ Critical Failure:\n`{error_detail}`")
    
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
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
