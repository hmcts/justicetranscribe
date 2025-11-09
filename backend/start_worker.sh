#!/bin/bash
set -e

# Force unbuffered output so logs appear immediately
export PYTHONUNBUFFERED=1

echo "🚀 Starting worker process..." >&2
echo "🚀 Starting worker process..."

echo "📊 Running database migrations..." >&2
echo "📊 Running database migrations..."
cd /app
/app/.venv/bin/alembic upgrade head 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully!" >&2
    echo "✅ Database migrations completed successfully!"
else
    echo "❌ Database migrations failed!" >&2
    echo "❌ Database migrations failed!"
    exit 1
fi

echo "⚙️  Starting transcription polling worker..." >&2
echo "⚙️  Starting transcription polling worker..."
exec /app/.venv/bin/python -u worker.py

