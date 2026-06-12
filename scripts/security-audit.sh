#!/bin/bash
# Fugue 安全审计脚本
# 用法: bash scripts/security-audit.sh

set -e

echo "=== Fugue Security Audit ==="
echo ""

# 1. Python 依赖审计
echo "[1/4] Python dependency audit..."
if command -v pip-audit &> /dev/null; then
    pip-audit -r backend/requirements.txt 2>&1 || echo "  ⚠ pip-audit found issues"
else
    echo "  ℹ pip-audit not installed. Install: pip install pip-audit"
    pip install pip-audit -q && pip-audit -r backend/requirements.txt 2>&1 || true
fi
echo ""

# 2. npm 依赖审计
echo "[2/4] npm dependency audit..."
cd frontend && npm audit --production 2>&1 | tail -5 || true
cd ..
echo ""

# 3. 检查硬编码密钥
echo "[3/4] Scanning for hardcoded secrets..."
FOUND=0
for pattern in "password\s*=\s*['\"]" "secret\s*=\s*['\"]" "api_key\s*=\s*['\"]" "token\s*=\s*['\"]"; do
    MATCHES=$(grep -rn --include="*.py" --include="*.ts" --include="*.tsx" -E "$pattern" backend/app/ frontend/src/ 2>/dev/null | grep -v "test" | grep -v "mock" | grep -v "example" | grep -v "placeholder" || true)
    if [ -n "$MATCHES" ]; then
        echo "  ⚠ Potential hardcoded secret:"
        echo "$MATCHES" | head -3
        FOUND=1
    fi
done
if [ $FOUND -eq 0 ]; then
    echo "  ✅ No hardcoded secrets found in source code"
fi
echo ""

# 4. 检查 .env 文件是否在 .gitignore
echo "[4/4] Checking .env in .gitignore..."
if grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo "  ✅ .env is in .gitignore"
else
    echo "  ⚠ .env may not be in .gitignore"
fi
echo ""

echo "=== Audit Complete ==="
