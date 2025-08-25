# syntax=docker/dockerfile:1
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

# Use the locked requirements for deterministic builds
COPY requirements.lock .

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

RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.lock

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
COPY requirements.lock .
RUN pip install --no-cache-dir --no-index --find-links=/wheels --require-hashes -r requirements.lock \
    && rm -rf /wheels requirements.lock

COPY . .

ENTRYPOINT ["os-guardian"]
