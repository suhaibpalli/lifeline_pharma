# ─────────────────────────────────────────────
# Stage 1: Builder — install deps + compile
# ─────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        libjpeg-dev \
        zlib1g-dev \
        libwebp-dev \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

COPY . .

# Install npm dependencies
RUN npm install

# Build full Tailwind CSS with all utilities -> tailwind.min.css
# (required for all Tailwind utility classes used in templates)
RUN npx tailwindcss -i ./static/src/input.css -o ./static/css/tailwind.min.css --minify

# Build custom.css with custom styles only (not full Tailwind)
# (custom animations, design system, etc.)
RUN npx tailwindcss -i ./static/src/input.css -o ./static/css/custom.css --minify

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

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        libjpeg62-turbo \
        zlib1g \
        libwebp7 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /install

RUN groupadd --gid 1001 pharma && \
    useradd --uid 1001 --gid pharma --shell /bin/bash --create-home pharma

RUN mkdir -p /app/staticfiles /app/logs && \
    chown -R pharma:pharma /app

COPY --chown=pharma:pharma . .

# Copy BOTH CSS files from builder
COPY --from=builder --chown=pharma:pharma /build/static/css/tailwind.min.css /app/static/css/tailwind.min.css
COPY --from=builder --chown=pharma:pharma /build/static/css/custom.css /app/static/css/custom.css

# Debug: verify files exist
RUN ls -la /app/static/css/ || echo "Directory not found"

RUN chmod +x entrypoint.sh

USER pharma

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["./entrypoint.sh"]
