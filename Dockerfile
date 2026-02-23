# استخدام نسخة بايثون رسمية وخفيفة
FROM python:3.10-slim

# تثبيت FFmpeg وتحديث النظام داخل الحاوية
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && apt-get clean \
    # تنظيف الملفات المؤقتة لتقليل حجم الصورة
    && rm -rf /var/lib/apt/lists/*

# تحديد مجلد العمل
WORKDIR /app

# نسخ ملف المكتبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ بقية ملفات الكود
COPY . .

# تشغيل البوت
CMD ["python", "app.py"]
