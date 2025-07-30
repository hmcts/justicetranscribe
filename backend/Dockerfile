FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies and uv
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

# Set the working directory
WORKDIR /app

# Copy only requirements to cache them in docker layer
COPY pyproject.toml uv.lock README.md ./

# Install project dependencies
RUN uv sync --frozen --no-dev --group fastapi

# Copy the FastAPI application code
COPY backend backend
COPY shared_utils shared_utils
COPY alembic alembic
COPY alembic.ini alembic.ini

# Expose the port the app runs on
EXPOSE 8080

RUN chmod +x backend/entrypoint.sh

HEALTHCHECK CMD curl --fail http://localhost:8080/healthcheck

ENTRYPOINT ["backend/entrypoint.sh"]