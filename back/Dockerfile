# ============================================
# Builder Stage - Install dependencies with uv
# ============================================
FROM python:3.13-bookworm AS builder

# Install tooling and uv CLI
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl ca-certificates build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv (astral) to manage dependencies
ADD https://astral.sh/uv/install.sh /install.sh
RUN chmod +x /install.sh && /install.sh && rm /install.sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

# Copy only dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync

# ============================================
# Development Stage - For local development with hot reload
# ============================================
FROM python:3.13-slim-bookworm AS development

RUN apt-get update \
    && apt-get install --no-install-recommends -y ca-certificates libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy venv from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser ./entrypoint.sh ./entrypoint.sh

RUN chmod +x ./entrypoint.sh

# Copy application code
COPY --chown=appuser:appuser ./app ./app

USER appuser

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONPATH="/app:${PYTHONPATH}" \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with hot reload for development
CMD ["/app/entrypoint.sh"]

