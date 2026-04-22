FROM python:3.12-slim

# Install system dependencies including liboqs
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    liboqs-dev \
    && rm -rf /var/lib/apt/lists/*

# Install liboqs-python
RUN pip install liboqs-python

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash qmind

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=qmind:qmind . .

# Switch to non-root user
USER qmind

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

CMD ["uvicorn", "enterprise_api:app", "--host", "0.0.0.0", "--port", "8001"]
