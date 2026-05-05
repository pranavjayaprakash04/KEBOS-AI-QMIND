FROM python:3.12-slim

# Install system dependencies and build liboqs from source
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    cmake \
    ninja-build \
    git \
    curl \
    python3-dev \
    liblz4-dev \
    && rm -rf /var/lib/apt/lists/*

# Build liboqs from source
RUN git clone --depth 1 --branch 0.12.0 https://github.com/open-quantum-safe/liboqs.git /tmp/liboqs

# Stage 1 — Build liboqs shared library
RUN cmake -S /tmp/liboqs -B /tmp/liboqs/build \
    -DBUILD_SHARED_LIBS=ON \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX=/usr/local \
    -DOQS_BUILD_ONLY_LIB=ON \
    -DOQS_USE_OPENSSL=OFF \
    && cmake --build /tmp/liboqs/build --parallel $(nproc) \
    && cmake --install /tmp/liboqs/build \
    && ldconfig \
    && rm -rf /tmp/liboqs

# Stage 2 — Force liboqs-python to use the installed .so
ENV LIBOQS_LIBDIR=/usr/local/lib
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH

# Install liboqs-python from PyPI but skip the bundled download
# Pin to 0.9.0 to match liboqs 0.12.0 (version compatibility)
RUN pip install liboqs-python==0.9.0 --no-binary liboqs-python \
    || pip install git+https://github.com/open-quantum-safe/liboqs-python.git@0.9.0

# Verify at build time — if this fails, the image fails to build
RUN python -c "import oqs; kem = oqs.KeyEncapsulation('Kyber768'); print('liboqs OK')"

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
