# اختيار نسخة بايثون مستقرة
FROM python:3.12-slim

# تحديث النظام وتثبيت الحزم الضرورية (Tesseract + FFMPEG + أدوات الاتصال)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-ara \
    tesseract-ocr-eng \
    ffmpeg \
    libssl-dev \
    libcurl4-openssl-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# إعداد المجلد
WORKDIR /app
COPY . .

# تثبيت المكتبات من requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# تشغيل البوت
CMD ["python", "Maxma1998-no.py"]
