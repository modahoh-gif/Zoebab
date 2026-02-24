import asyncio
import os
import yt_dlp
import psycopg2 # تأكد من تثبيت psycopg2-binary
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters

# الإعدادات
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))
COOKIES_CONTENT = os.getenv("YT_COOKIES")
DATABASE_URL = "postgresql://neondb_owner:npg_FX12aBqMvtyJ@ep-steep-thunder-adoapjc4-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require"

# --- وظائف قاعدة البيانات ---

def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY)''')
    conn.commit()
    cur.close()
    conn.close()

def add_user(user_id):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO users (user_id) VALUES (%s) ON CONFLICT (user_id) DO NOTHING", (user_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

def get_user_count():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

# --- مهام البوت ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    welcome_text = (
        f"👋 أهلاً بك يا {update.effective_user.first_name} في بوت تحميل صوتيات يوتيوب!\n\n"
        "🚀 أرسل لي رابط فيديو من يوتيوب وسأقوم بتحويله إلى MP3 وإرساله لك."
    )
    await update.message.reply_text(welcome_text)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = get_user_count()
    await update.message.reply_text(f"📊 إحصائيات البوت:\n\n👥 عدد المستخدمين: {count}")

async def download_audio_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # إضافة المستخدم للقاعدة حتى لو لم يضغط start (اختياري)
    add_user(update.effective_user.id)
    
    url = update.message.text.strip()
    status_msg = await update.message.reply_text("⏳ جاري معالجة الرابط وتحميل الصوت...")

    unique_id = str(update.message.message_id)
    filename = f"audio_{unique_id}"
    cookie_path = f"cookies_{unique_id}.txt"

    try:
        if COOKIES_CONTENT:
            with open(cookie_path, "w", encoding="utf-8") as f:
                f.write(COOKIES_CONTENT.strip() + "\n")

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": f"{filename}.%(ext)s",
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "cookiefile": cookie_path if COOKIES_CONTENT else None,
            "nocheckcertificate": True,
            "retries": 10,
            "fragment_retries": 10,
            "age_limit": 100,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "http_headers": {"User-Agent": "Mozilla/5.0"},
        }

        def run_dl():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        await asyncio.to_thread(run_dl)

        expected_file = f"{filename}.mp3"
        if os.path.exists(expected_file):
            await status_msg.edit_text("✅ تم التحميل! جاري إرسال الملف...")
            with open(expected_file, "rb") as audio:
                await update.message.reply_audio(audio=audio, caption="تم التحميل بواسطة بوتك 🚀")
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ فشل استخراج الصوت. تأكد من إعدادات FFmpeg.")

    except Exception as e:
        await status_msg.edit_text(f"❌ خطأ غير متوقع:\n`{str(e)[:300]}`", parse_mode="Markdown")

    finally:
        if os.path.exists(cookie_path): os.remove(cookie_path)
        for ext in ["mp3", "webm", "m4a", "mp4", "part"]:
            f = f"{filename}.{ext}"
            if os.path.exists(f): os.remove(f)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" in url or "youtu.be" in url:
        asyncio.create_task(download_audio_task(update, context))
    else:
        await update.message.reply_text("⚠️ من فضلك أرسل رابط يوتيوب صحيح.")

def main():
    # تهيئة القاعدة
    init_db()

    app = Application.builder().token(TOKEN).build()
    
    # الـ Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # تشغيل البوت
    print("Bot is starting...")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}",
    )

if __name__ == "__main__":
    main()
