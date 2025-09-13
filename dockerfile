FROM python:3.11-slim

WORKDIR /app

# Sistem bağımlılıkları (psycopg2 için gerekli)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Koyeb portu 8080 olmalı
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
