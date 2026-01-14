# Multi-stage Dockerfile for Turbo Code API
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Set work directory
WORKDIR /app

# Copy requirements files
COPY pyproject.toml ./

# Install Python dependencies including docs
RUN pip install --no-cache-dir -e ".[docs]"

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    TURBO_ENVIRONMENT=production

# Install runtime dependencies (including PyTorch/torchaudio requirements, git for worktrees, and WeasyPrint dependencies)
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    libgomp1 \
    libsndfile1 \
    ffmpeg \
    git \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libffi-dev \
    libjpeg-dev \
    libopenjp2-7 \
    && rm -rf /var/lib/apt/lists/*

# Create app user with home directory
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# Set work directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code and docs
COPY --chown=appuser:appuser . .

# Build documentation if mkdocs.yml exists
RUN if [ -f mkdocs.yml ]; then mkdocs build; fi

# Create necessary directories
RUN mkdir -p /app/.turbo /app/logs && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Default command - run API server
CMD ["uvicorn", "turbo.main:app", "--host", "0.0.0.0", "--port", "8000"]