# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS runtime
ARG EXTRA_REQUIREMENTS=""
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg sox && \
    rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --shell /bin/bash inanna
WORKDIR /home/inanna/app
COPY . .
RUN if [ -n "$EXTRA_REQUIREMENTS" ]; then pip install --no-cache-dir -r $EXTRA_REQUIREMENTS; fi
RUN chown -R inanna:inanna /home/inanna/app
USER inanna
HEALTHCHECK --interval=30s --timeout=3s CMD \
    curl -f http://localhost:8000/health || exit 1
ENTRYPOINT ["bash", "run_inanna.sh"]
