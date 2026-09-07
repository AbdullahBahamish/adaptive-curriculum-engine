# =============================================================================
# Multi-stage Dockerfile for the ACE AI Engine
# =============================================================================

# Stage 1: Builder — install dependencies
FROM python:3.13-slim AS builder

WORKDIR /build

COPY pyproject.toml .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir build \
    && pip install --no-cache-dir ".[dev]" --target /build/deps

# Stage 2: Production image
FROM python:3.13-slim AS production

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /build/deps /usr/local/lib/python3.13/site-packages

# Copy application configuration and source
COPY pyproject.toml .
COPY alembic.ini .
COPY alembic/ alembic/
COPY src/ src/
COPY data/ data/
COPY scripts/ scripts/

# Install the package in editable mode
RUN pip install --no-cache-dir -e . --no-deps

EXPOSE 8000

# Run database migrations, seed data if needed, then start the server
CMD ["sh", "-c", "alembic upgrade head && python scripts/seed.py && uvicorn ace.api.main:app --host 0.0.0.0 --port 8000"]