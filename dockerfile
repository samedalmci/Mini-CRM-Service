# Daha kapsamlı bir Python image kullanıyoruz
FROM python:3.11

WORKDIR /app

# Sistem bağımlılıkları (Torch, Transformers için gerekli)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]


