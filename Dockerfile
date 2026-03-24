# ─────────────────────────────────────────────
# Stage 1: Builder — install deps + compile
# ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# System deps needed to compile psycopg2, Pillow etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
        libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip once in builder
RUN pip install --upgrade pip

# Copy only requirements — layer cache: this only re-runs when requirements.txt changes
COPY requirements.txt .

# Install all packages into a prefix dir (not system) so we can copy cleanly
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ─────────────────────────────────────────────
# Stage 2: Runtime — lean final image
# ─────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.12/site-packages"

# Only runtime system libs needed (no gcc, no dev headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        zlib1g \
        libwebp7 \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled packages from builder
COPY --from=builder /install /install

# Create non-root user — never run as root in production
RUN groupadd --gid 1001 pharma && \
    useradd --uid 1001 --gid pharma --shell /bin/bash --create-home pharma

# Create dirs and set ownership before copying code
RUN mkdir -p /app/staticfiles /app/logs && \
    chown -R pharma:pharma /app

# Copy project code
COPY --chown=pharma:pharma . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Switch to non-root
USER pharma

# Expose app port
EXPOSE 8000

# Health check — Django must have a /health/ endpoint (add below)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Entrypoint script handles migrations + collectstatic before gunicorn
ENTRYPOINT ["./entrypoint.sh"]
