# =============================================================================
# Multi-stage Dockerfile for the ACE AI Engine
# =============================================================================

# Stage 1: Builder — install dependencies
FROM python:3.13-slim AS builder

WORKDIR /build

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md ./
COPY src/ src/

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
    && pip install --default-timeout=120 --retries=10 ".[dev]"

# Stage 2: Production image
FROM python:3.13-slim AS production

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application configuration and source
COPY pyproject.toml README.md alembic.ini ./
COPY alembic/ alembic/
COPY src/ src/
COPY data/ data/
COPY scripts/ scripts/

# Install the package in editable mode
RUN pip install --no-cache-dir -e . --no-deps

EXPOSE 8000

# Run database migrations, seed data if needed, then start the server
CMD ["sh", "-c", "alembic upgrade head && python scripts/seed.py && uvicorn ace.api.main:app --host 0.0.0.0 --port 8000"]