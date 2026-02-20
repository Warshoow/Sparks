# =============================================================================
# Social Content Archiver - Dockerfile
# Multi-stage build for optimized image size
# =============================================================================

# ---------------------
# Stage 1: Builder
# ---------------------
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Download spaCy model
RUN pip install --no-cache-dir --prefix=/install spacy \
    && python -m spacy download en_core_web_sm

# Pre-download Faster-Whisper model (optional, avoids download at first run)
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" || true

# ---------------------
# Stage 2: Runtime
# ---------------------
FROM python:3.11-slim AS runtime

LABEL maintainer="Social Content Archiver"
LABEL version="0.1.0"

# Install system dependencies for runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-eng \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Create directories for persistent data
RUN mkdir -p /app/data /app/archives /app/media /app/logs

# Copy application code
COPY src/ ./src/
COPY config/ ./config/
COPY setup.py .

# Default environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATABASE_URL=sqlite:////app/data/archive.db \
    ARCHIVE_PATH=/app/archives \
    MEDIA_PATH=/app/media \
    REDIS_URL=redis://redis:6379/0 \
    LLM_PROVIDER=openai \
    TRANSCRIPTION_PROVIDER=openai

# Volumes for persistent data
VOLUME ["/app/data", "/app/archives", "/app/media", "/app/logs"]

ENTRYPOINT ["python", "-m", "src.main"]
CMD ["run"]
