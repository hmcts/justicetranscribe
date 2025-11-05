#!/bin/bash
set -e

echo "🚀 Starting backend application..."

echo "🔍 Checking for missing migrations..."
cd /app
/app/.venv/bin/python scripts/fix_missing_migration.py

if [ $? -eq 0 ]; then
    echo "✅ Migration state check completed!"
else
    echo "⚠️  Migration state check had issues, but continuing..."
fi

echo "📊 Running database migrations..."
/app/.venv/bin/alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully!"
else
    echo "❌ Database migrations failed!"
    exit 1
fi

echo "🌐 Starting FastAPI server..."
exec /app/.venv/bin/fastapi run main.py --port 80 