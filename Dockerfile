# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Select extras to install via build argument. Defaults to the minimal set.
ARG EXTRAS="minimal"

COPY . .
RUN pip install --no-cache-dir .[${EXTRAS}]

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ffmpeg sox && \
    rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash inanna && \
    chown -R inanna:inanna /app
USER inanna
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=3s CMD \
    curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["bash", "run_inanna.sh"]
