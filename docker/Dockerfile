FROM python:3.11-slim

WORKDIR /workspace

# Prevent python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace

# Accept Git commit hash at build time for deploy verification (/version endpoint)
ARG GIT_COMMIT=dev-local
ENV GIT_COMMIT=${GIT_COMMIT}

# Apply base OS security updates (patches CVE-2026-85091 in zlib1g) and install curl
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application and source files
COPY src/ ./src/
COPY app/ ./app/
COPY tests/ ./tests/

# Ensure data and models directories exist and train base model artifact
RUN mkdir -p data models
RUN python -m src.train

# Security hardening: remove build-time packaging tools (setuptools, wheel)
# Eliminates CVE-2025-47273 and reduces runtime attack surface
RUN pip uninstall -y setuptools wheel || true \
    && rm -rf /usr/lib/python3/dist-packages/setuptools* \
              /usr/local/lib/python3.11/site-packages/setuptools* \
              /usr/local/lib/python3.11/site-packages/wheel*

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=20s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start inference server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
