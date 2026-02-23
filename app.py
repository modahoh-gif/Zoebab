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

# جلب المتغيرات من إعدادات رندر
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))
# تأكد من لصق محتوى ملف الكوكيز بالكامل في هذا المتغير في رندر
COOKIES_CONTENT = os.getenv("YT_COOKIES")

async def download_audio_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة التحميل التي تعمل في الخلفية"""
    url = update.message.text
    status_msg = await update.message.reply_text("⏳ Processing your request... Please wait.")
    
    unique_id = str(update.message.message_id)
    filename = f"audio_{unique_id}"
    cookie_path = f"cookies_{unique_id}.txt"

    try:
        # 1. إنشاء ملف الكوكيز ومعالجة التنسيق
        if COOKIES_CONTENT:
            with open(cookie_path, "w", encoding="utf-8") as f:
                # تنظيف النص لضمان توافقه مع تنسيق Netscape
                f.write(COOKIES_CONTENT.strip())
                f.write("\n")

        # 2. إعدادات yt-dlp المحسنة
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{filename}.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "cookiefile": cookie_path if COOKIES_CONTENT else None,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            # خيارات إضافية لتفادي الحظر
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            }
        }

        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        # تشغيل التحميل دون تجميد البوت
        await asyncio.to_thread(run_dl)
        
        expected_file = f"{filename}.mp3"
        
        if os.path.exists(expected_file):
            await status_msg.edit_text("✅ Downloaded! Uploading to Telegram...")
            with open(expected_file, "rb") as audio:
                await update.message.reply_audio(
                    audio=audio,
                    caption=f"🎵 Successfully Downloaded\n🔗 {url}"
                )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Error: Could not process audio. Ensure FFmpeg is active.")

    except Exception as e:
        error_msg = str(e)
        if "cookies" in error_msg.lower():
            await status_msg.edit_text("❌ Cookie Format Error: Please re-export cookies from Kiwi Browser in 'Netscape' format.")
        else:
            await status_msg.edit_text(f"❌ Failed: {error_msg[:100]}")
    
    finally:
        # تنظيف الملفات المؤقتة دائماً
        if os.path.exists(f"{filename}.mp3"): os.remove(f"{filename}.mp3")
        if os.path.exists(cookie_path): os.remove(cookie_path)
        # حذف الملفات الأصلية إذا بقيت (مثل .webm أو .m4a)
        for ext in ['webm', 'm4a', 'ytdl']:
            if os.path.exists(f"{filename}.{ext}"): os.remove(f"{filename}.{ext}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استلام الرسالة والرد السريع لتجنب Webhook Timeout"""
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        # البدء في مهمة التحميل بشكل منفصل
        asyncio.create_task(download_audio_task(update, context))
    else:
        await update.message.reply_text("❌ Please send a valid YouTube link.")

def main():
    if not TOKEN or not WEBHOOK_URL:
        print("CRITICAL ERROR: BOT_TOKEN or WEBHOOK_URL not set in Environment Variables.")
        return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"Bot is starting on port {PORT} via Webhook...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
