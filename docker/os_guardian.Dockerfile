# syntax=docker/dockerfile:1
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY requirements.txt .

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ffmpeg \
        tesseract-ocr \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgtk-3-0 \
        libnss3 \
        libxrandr2 \
        libasound2 \
        libxi6 \
        scrot \
        x11-apps \
        firefox-esr \
    && rm -rf /var/lib/apt/lists/*

RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        tesseract-ocr \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgtk-3-0 \
        libnss3 \
        libxrandr2 \
        libasound2 \
        libxi6 \
        scrot \
        x11-apps \
        firefox-esr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && rm -rf /wheels

COPY . .

ENTRYPOINT ["os-guardian"]
