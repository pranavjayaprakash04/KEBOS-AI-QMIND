FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash kebos

WORKDIR /app

# Copy requirements and install
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application code
COPY --chown=kebos:kebos . .

# Copy alembic.ini for migrations
COPY --chown=kebos:kebos alembic.ini /app/

# Switch to non-root user
USER kebos

# Security options
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
