# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS deps
COPY . .
RUN pip install --no-cache-dir .[audio,vision,llm,ml,web,network]

FROM deps AS runtime
ARG EXTRA_REQUIREMENTS=""
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl ffmpeg sox && \
    rm -rf /var/lib/apt/lists/*
RUN if [ -n "$EXTRA_REQUIREMENTS" ]; then pip install --no-cache-dir -r $EXTRA_REQUIREMENTS; fi
RUN useradd --create-home --shell /bin/bash inanna && \
    chown -R inanna:inanna /app
USER inanna
WORKDIR /app
HEALTHCHECK --interval=30s --timeout=3s CMD \
    curl -f http://localhost:8000/health || exit 1
ENTRYPOINT ["bash", "run_inanna.sh"]
