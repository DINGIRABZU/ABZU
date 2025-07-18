# syntax=docker/dockerfile:1
FROM python:3.10-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash inanna
WORKDIR /home/inanna/app

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

COPY . .

RUN chown -R inanna:inanna /home/inanna/app
USER inanna

HEALTHCHECK --interval=30s --timeout=3s CMD \
    curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["bash", "run_inanna.sh"]
