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

echo "🌐 Starting FastAPI server..."
exec /app/.venv/bin/fastapi run app/main.py --port 80 