#!/bin/bash

# 前端快速诊断脚本

echo "========================================"
echo "  Frontend Diagnosis Script"
echo "========================================"
echo ""

# 检查Docker服务状态
echo "[1/5] Checking Docker services..."
docker compose ps
echo ""

# 检查前端容器日志
echo "[2/5] Checking frontend container logs..."
docker compose logs frontend --tail=20
echo ""

# 检查TypeScript编译错误
echo "[3/5] Checking for TypeScript errors..."
docker compose exec frontend npm run build 2>&1 | head -50
echo ""

# 检查文件权限
echo "[4/5] Checking file permissions..."
ls -la frontend/src/hooks/useWebSocket.ts
ls -la frontend/src/hooks/useExecutionMonitor.ts
ls -la frontend/src/components/monitor/RealtimeThoughts.tsx
echo ""

# 重启前端服务
echo "[5/5] Restarting frontend service..."
docker compose restart frontend
echo ""

echo "========================================"
echo "  Diagnosis Complete"
echo "========================================"
echo ""
echo "Try accessing: http://localhost:3000"
echo ""
echo "If still having issues:"
echo "1. Clear browser cache (Ctrl+Shift+Delete)"
echo "2. Open in incognito mode (Ctrl+Shift+N)"
echo "3. Check browser console (F12) for errors"
echo ""
