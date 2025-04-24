FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

RUN apt-get update && \
    apt-get install -y \
    libglib2.0-0 \
    libglib2.0-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

CMD ["python", "app/bot.py"]