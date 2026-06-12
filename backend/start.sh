#!/bin/bash
set -e

echo "🚀 Starting Fugue backend..."

# 等待数据库就绪
echo "⏳ Waiting for database..."
sleep 5

# 运行数据库迁移
echo "📦 Running database migrations..."
alembic upgrade head || echo "⚠️ Migration failed or already up to date"

# 启动应用
echo "✅ Starting FastAPI server..."
exec uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
