import asyncio
import os
import yt_dlp
from telegram import Update
from telegram.ext import ContextTypes

async def download_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("الرجاء إرسال رابط يوتيوب صحيح")
        return

    status_msg = await update.message.reply_text("جاري المعالجة والتحميل... ⏳")

    # إعدادات محسنة
    unique_id = str(update.message.message_id) # لضمان عدم تداخل الملفات إذا طلب أكثر من شخص في نفس الوقت
    filename = f"audio_{unique_id}"
    
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{filename}.%(ext)s", # اسم فريد
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        def download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        # تشغيل التحميل في Thread منفصل
        await asyncio.to_thread(download)
        
        expected_file = f"{filename}.mp3"

        if os.path.exists(expected_file):
            await status_msg.edit_text("جاري رفع الملف إلى تليجرام... ⬆️")
            with open(expected_file, "rb") as audio:
                await update.message.reply_audio(audio=audio)
            os.remove(expected_file)
            await status_msg.delete() # حذف رسالة "جاري التحميل" بعد الانتهاء
        else:
            await status_msg.edit_text("عذراً، حدث خطأ أثناء معالجة الملف.")

    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text(f"حدث خطأ غير متوقع: {str(e)}")
        # تنظيف أي ملفات متبقية في حال الخطأ
        if os.path.exists(f"{filename}.mp3"):
            os.remove(f"{filename}.mp3")
