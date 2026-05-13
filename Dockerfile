# ---------------------------------------------------------
# Stage 1 - Build Dependencies
# ---------------------------------------------------------

FROM python:3.12-slim AS builder

# Prevent Python from writing pyc files
ENV PYTHONDONTWRITEBYTECODE=1

# Ensure stdout/stderr are unbuffered
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for Docker layer caching
COPY requirements.txt .

# Create virtual environment
RUN python -m venv /opt/venv

# Install dependencies
RUN /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# ---------------------------------------------------------
# Stage 2 - Runtime Image
# ---------------------------------------------------------

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Security: create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Add venv to PATH
ENV PATH="/opt/venv/bin:$PATH"

# Copy application source
COPY . .

# Security: change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/live')" || exit 1

# Production startup command
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "main:app"]