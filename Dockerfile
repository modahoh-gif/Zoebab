# اختيار نظام تشغيل خفيف يحتوي على بايثون
FROM python:3.10-slim

# إعداد بيئة ثابتة، تحديث النظام وتثبيت الأدوات الضرورية
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    wget \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# تعيين مجلد العمل
WORKDIR /app

# نسخ ملفات المتطلبات وتثبيت المكتبات
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# تحديث yt-dlp لأحدث نسخة (لحماية ضد تغييرات YouTube)
RUN pip install --upgrade yt-dlp

# نسخ الكود
COPY . .

# البيئة الافتراضية لتجنب مشاكل الترميز
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Expose البورت (اختياري حسب Webhook)
EXPOSE 10000

# تشغيل البوت
CMD ["python", "app.py"]
