# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir .[llm]
ENV PYTHONPATH=/app/src
CMD ["python", "invocation_engine.py"]
