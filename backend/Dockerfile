FROM python:3.12-slim-bullseye

# Install system dependencies including curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy the application into the container.
COPY . /app

# Install the application dependencies including fastapi group for alembic, excluding dev
WORKDIR /app
RUN uv sync --frozen --no-cache --group fastapi --no-group dev

# Make the unified validation script executable
RUN chmod +x /app/build_utils/validate_config.py

# Copy and make the startup scripts executable
COPY start.sh /app/start.sh
COPY start_worker.sh /app/start_worker.sh
RUN chmod +x /app/start.sh /app/start_worker.sh

# Run the startup script (which handles migrations + server startup)
# For worker, override CMD in docker-compose or Azure with /app/start_worker.sh
CMD ["/app/start.sh"]
