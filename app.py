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

# جلب المتغيرات من البيئة
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") # تأكد أنه يبدأ بـ https://
PORT = int(os.environ.get("PORT", 10000))

async def download_audio_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هذه الدالة تقوم بالعمل الثقيل في الخلفية"""
    url = update.message.text
    status_msg = await update.message.reply_text("جاري المعالجة... قد يستغرق الأمر دقيقة ⏳")
    
    unique_id = str(update.message.message_id)
    filename = f"audio_{unique_id}"

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{filename}.%(ext)s",
        "quiet": True,
        # محاكاة جوال لتجنب حظر IP السيرفر (بديل الكوكيز)
        "user_agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
        "extractor_args": {"youtube": {"player_client": ["ios", "android"]}},
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }

    try:
        # تشغيل التحميل في Thread منفصل لعدم تجميد البوت
        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await asyncio.to_thread(run_dl)
        
        expected_file = f"{filename}.mp3"
        if os.path.exists(expected_file):
            await status_msg.edit_text("تم التحميل بنجاح! جاري الإرسال... ⬆️")
            with open(expected_file, "rb") as audio:
                await update.message.reply_audio(audio=audio, caption="تم بواسطة بوتك ✅")
            os.remove(expected_file)
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ حدث خطأ في تحويل الملف (تأكد من وجود FFmpeg)")

    except Exception as e:
        await status_msg.edit_text(f"❌ فشل التحميل. يوتيوب قد يطلب كوكيز.\nالسبب: {str(e)[:50]}")
        if os.path.exists(f"{filename}.mp3"): os.remove(f"{filename}.mp3")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هذه الدالة تستقبل الرسالة وترد بسرعة لتجنب Webhook Timeout"""
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        # تشغيل دالة التحميل كـ Task منفصلة فوراً
        asyncio.create_task(download_audio_task(update, context))
    else:
        await update.message.reply_text("أرسل رابط يوتيوب صحيح من فضلك.")

def main():
    if not TOKEN or not WEBHOOK_URL:
        print("خطأ: يرجى ضبط BOT_TOKEN و WEBHOOK_URL في إعدادات Render")
        return

    app = Application.builder().token(TOKEN).build()
    
    # استخدام handle_message بدلاً من download_audio مباشرة
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"Starting Webhook on port {PORT}...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )

if __name__ == "__main__":
    main()
