FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    git \
    build-essential \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# تحديث yt-dlp
RUN pip install --upgrade yt-dlp

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

EXPOSE 10000

CMD ["python", "app.py"]
