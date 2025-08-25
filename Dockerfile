FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip curl && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    rm -rf /var/lib/apt/lists/*

# Install pinned dependencies from the lock file
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir --require-hashes -r requirements.lock

COPY . .

RUN python -m pip install --no-cache-dir --no-deps .

RUN useradd --create-home --shell /bin/bash inanna && \
    chown -R inanna:inanna /app
USER inanna
WORKDIR /app

HEALTHCHECK --interval=30s --timeout=3s CMD \
    curl -f http://localhost:8000/health || exit 1

ENTRYPOINT ["bash", "run_inanna.sh"]
