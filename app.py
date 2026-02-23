import os
from flask import Flask, request
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# إعدادات البوت
TOKEN = "7924976888:AAGOQMEmMOhx8IJblL0oZ9rDafc6uVXQNNY"
URL = "https://your-app-name.onrender.com" # سنغير هذا لاحقاً برابط ريندر

app = Flask(__name__)

# بناء التطبيق
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك! أرسل رابط يوتيوب وسأقوم بتحويله (تجريبي).")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "youtube.com" in text or "youtu.be" in text:
        await update.message.reply_text(f"جاري معالجة الرابط: {text}\n(ملاحظة: تحتاج لإضافة مكتبة yt-dlp للتحميل الفعلي)")
    else:
        await update.message.reply_text("من فضلك أرسل رابط يوتيوب صحيح.")

# إضافة الأوامر
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route(f'/{TOKEN}', methods=['POST'])
async def respond():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return 'ok'

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    import asyncio
    webhook_url = f"{URL}/{TOKEN}"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    s = loop.run_until_complete(application.bot.set_webhook(webhook_url))
    if s:
        return "Webhook setup successful"
    else:
        return "Webhook setup failed"

@app.route('/')
def index():
    return 'Bot is running...'

if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT', 5000)))
