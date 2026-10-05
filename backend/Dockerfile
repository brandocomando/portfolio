# syntax=docker/dockerfile:1
# Multi-stage minimal production container for Cloud Run (Scale-to-Zero)

# ==========================================
# Stage 1: Build Dependencies
# ==========================================
FROM python:3.10-slim as builder

WORKDIR /build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend-requirements.txt
COPY mlops/requirements.txt ./mlops-requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r backend-requirements.txt -r mlops-requirements.txt

# ==========================================
# Stage 2: Final Minimal Runtime
# ==========================================
FROM python:3.10-slim as runtime

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080

# Security: Run as non-root user
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/sh -m appuser

# Copy installed wheels from builder
COPY --from=builder /install /usr/local

# Copy application source code and gold MLOps index
COPY backend /app/backend
COPY mlops /app/mlops

# Ownership
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')" || exit 1

ENTRYPOINT ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8080"]
