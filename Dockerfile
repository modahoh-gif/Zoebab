# اختيار نظام تشغيل خفيف يحتوي على بايثون
FROM python:3.10-slim

# تحديث النظام وتثبيت FFmpeg (ضروري جداً لتحويل الصيغ)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# تثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# تشغيل البوت
CMD ["python", "app.py"]
