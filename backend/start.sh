#!/bin/bash
set -e

echo "🚀 Starting backend application..."

echo "📊 Running database migrations..."
cd /app
/app/.venv/bin/alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully!"
else
    echo "❌ Database migrations failed!"
    exit 1
fi

echo "🌐 Starting FastAPI server with production Uvicorn..."
exec /app/.venv/bin/uvicorn main:app \
    --host 0.0.0.0 \
    --port 80 \
    --workers 2 \
    --timeout-keep-alive 75 \
    --timeout-graceful-shutdown 30 \
    --limit-concurrency 1000 \
    --limit-max-requests 10000 \
    --log-level info 