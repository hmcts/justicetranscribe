#!/bin/bash

# Function to run database migrations
run_migrations() {
    echo "Running database migrations..."
    uv run alembic upgrade head
    if [ $? -ne 0 ]; then
        echo "Database migration failed!"
        exit 1
    fi
    echo "Database migrations completed successfully"
}

# Function to start the FastAPI application
start_app() {
    echo "Starting FastAPI application..."
    uv run uvicorn backend.main:app --host 0.0.0.0 --port 8080 &
    PID=$!
    wait $PID
}

# Main execution
run_migrations
start_app