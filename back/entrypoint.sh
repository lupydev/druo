#!/bin/sh
set -e  # Exit on error

echo "🔧 Running entrypoint..."

# Wait for database to be ready (simple retry loop)
echo "⏳ Waiting for database..."
MAX_RETRIES=30
RETRY_COUNT=0

until python -c "
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    url = os.getenv('DATABASE_URL', '').replace('postgresql://', 'postgresql+asyncpg://', 1)
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        await conn.execute(__import__('sqlalchemy').text('SELECT 1'))
    await engine.dispose()

asyncio.run(check())
" 2>/dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo "❌ Database not available after $MAX_RETRIES attempts"
        exit 1
    fi
    echo "  Attempt $RETRY_COUNT/$MAX_RETRIES..."
    sleep 1
done

echo "✅ Database is ready!"

# Apply seeds (idempotent - safe to run multiple times)
echo "🌱 Applying seeds..."
python -m app.core.seeds

# Start FastAPI server
echo "🚀 Starting FastAPI server..."

# Detecta el entorno (por defecto: development)
ENV=${ENVIRONMENT:-development}

if [ "$ENV" = "production" ]; then
    echo "🚀 Running in PRODUCTION mode"
    exec fastapi run app/main.py --host 0.0.0.0
else
    echo "👾 Running in DEVELOPMENT mode (with auto-reload)"
    exec fastapi dev app/main.py --host 0.0.0.0
fi
