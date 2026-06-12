#!/bin/bash

# Fugue 项目完整性检查脚本

set -e

echo "🔍 Fugue Project Integrity Check"
echo "======================================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARN++))
}

echo ""
echo "📁 Checking project structure..."
echo "--------------------------------"

# 检查核心目录
if [ -d "backend" ]; then
    check_pass "backend/ directory exists"
else
    check_fail "backend/ directory missing"
fi

if [ -d "frontend" ]; then
    check_pass "frontend/ directory exists"
else
    check_fail "frontend/ directory missing"
fi

if [ -d "tests" ]; then
    check_pass "tests/ directory exists"
else
    check_warn "tests/ directory missing"
fi

if [ -d "docs" ]; then
    check_pass "docs/ directory exists"
else
    check_warn "docs/ directory missing"
fi

echo ""
echo "📄 Checking essential files..."
echo "-------------------------------"

# 检查核心文件
essential_files=(
    "README.md"
    "docker-compose.yml"
    ".env.example"
    "backend/Dockerfile"
    "backend/requirements.txt"
    "backend/pyproject.toml"
    "frontend/package.json"
    "backend/app/main.py"
    "frontend/src/App.tsx"
)

for file in "${essential_files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_fail "$file missing"
    fi
done

echo ""
echo "🔧 Checking configuration files..."
echo "-----------------------------------"

# 检查配置文件
config_files=(
    ".env.example"
    "docker-compose.yml"
    "backend/alembic.ini"
    "backend/.env.example"
    "frontend/vite.config.ts"
    "frontend/tsconfig.json"
)

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_warn "$file missing"
    fi
done

echo ""
echo "📚 Checking documentation..."
echo "-----------------------------"

# 检查文档
doc_files=(
    "README.md"
    "CONTRIBUTING.md"
    "docs/QUICK_START.md"
    "docs/DEPLOYMENT.md"
    "docs/DEMO_GUIDE.md"
    "docs/SECURITY_CHECKLIST.md"
    "项目计划书_Fugue.md"
)

for file in "${doc_files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_warn "$file missing"
    fi
done

echo ""
echo "🧪 Checking test files..."
echo "--------------------------"

# 检查测试文件
test_files=(
    "tests/e2e_test.py"
    "backend/tests/conftest.py"
    "backend/tests/test_auth.py"
    "backend/tests/test_crews.py"
    "backend/tests/test_agents.py"
    "backend/tests/test_tasks.py"
    "backend/tests/test_executions.py"
    "backend/tests/test_templates.py"
    "backend/tests/test_validation.py"
)

for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
    else
        check_warn "$file missing"
    fi
done

echo ""
echo "🚀 Checking scripts..."
echo "-----------------------"

# 检查脚本
scripts=(
    "run_tests.sh"
    "docker-start.sh"
    "docker-start.bat"
    "start-dev.sh"
    "start-dev.bat"
)

for file in "${scripts[@]}"; do
    if [ -f "$file" ]; then
        check_pass "$file exists"
        # 检查可执行权限（仅Linux/macOS）
        if [[ "$OSTYPE" != "msys" && "$OSTYPE" != "win32" ]]; then
            if [ -x "$file" ] || [[ "$file" == *.bat ]]; then
                check_pass "$file is executable"
            else
                check_warn "$file not executable (run: chmod +x $file)"
            fi
        fi
    else
        check_warn "$file missing"
    fi
done

echo ""
echo "📦 Checking backend dependencies..."
echo "------------------------------------"

if [ -f "backend/requirements.txt" ]; then
    check_pass "requirements.txt exists"
    dep_count=$(grep -c "^[^#]" backend/requirements.txt || echo 0)
    echo "   📊 Found $dep_count dependencies"
fi

if [ -f "backend/pyproject.toml" ]; then
    check_pass "pyproject.toml exists"
fi

echo ""
echo "🎨 Checking frontend dependencies..."
echo "-------------------------------------"

if [ -f "frontend/package.json" ]; then
    check_pass "package.json exists"
    if [ -d "frontend/node_modules" ]; then
        check_pass "node_modules exists"
    else
        check_warn "node_modules missing (run: cd frontend && npm install)"
    fi
fi

echo ""
echo "🐳 Checking Docker configuration..."
echo "-------------------------------------"

if [ -f "docker-compose.yml" ]; then
    check_pass "docker-compose.yml exists"

    # 检查关键服务配置
    if grep -q "postgres:" docker-compose.yml; then
        check_pass "PostgreSQL service configured"
    else
        check_warn "PostgreSQL service not found"
    fi

    if grep -q "redis:" docker-compose.yml; then
        check_pass "Redis service configured"
    else
        check_warn "Redis service not found"
    fi

    if grep -q "backend:" docker-compose.yml; then
        check_pass "Backend service configured"
    else
        check_warn "Backend service not found"
    fi

    if grep -q "frontend:" docker-compose.yml; then
        check_pass "Frontend service configured"
    else
        check_warn "Frontend service not found"
    fi
fi

echo ""
echo "📊 Summary"
echo "=========="
echo -e "✅ Passed: ${GREEN}$PASS${NC}"
echo -e "❌ Failed: ${RED}$FAIL${NC}"
echo -e "⚠️  Warnings: ${YELLOW}$WARN${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 Project integrity check passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Project integrity check failed with $FAIL errors${NC}"
    exit 1
fi
