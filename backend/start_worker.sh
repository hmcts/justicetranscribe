#!/bin/bash
set -e

echo "🚀 Starting worker process..."

echo "📊 Running database migrations..."
cd /app
/app/.venv/bin/alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully!"
else
    echo "❌ Database migrations failed!"
    exit 1
fi

echo "⚙️  Starting transcription polling worker..."
exec /app/.venv/bin/python worker.py

