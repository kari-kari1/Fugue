#!/bin/bash

# Fugue 测试运行脚本

set -e

echo "🧪 Fugue 测试套件"
echo "========================"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 函数：打印成功消息
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 函数：打印错误消息
error() {
    echo -e "${RED}❌ $1${NC}"
}

# 函数：打印警告消息
warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 检查是否安装了必要的依赖
check_dependencies() {
    echo "检查依赖..."

    if ! command -v python3 &> /dev/null; then
        error "Python3 未安装"
        exit 1
    fi

    if ! command -v pytest &> /dev/null; then
        warn "pytest 未找到，尝试安装..."
        pip install pytest pytest-asyncio pytest-cov
    fi

    success "依赖检查完成"
}

# 运行后端单元测试
run_backend_tests() {
    echo ""
    echo "📦 运行后端测试..."
    echo "-------------------"

    cd backend

    # 安装测试依赖
    pip install -e ".[dev]" -q

    # 运行测试
    if pytest tests/ -v --tb=short --cov=app --cov-report=html --cov-report=term-missing; then
        success "后端测试通过"
    else
        error "后端测试失败"
        cd ..
        return 1
    fi

    cd ..
    return 0
}

# 运行端到端测试（需要运行的服务）
run_e2e_tests() {
    echo ""
    echo "🔗 运行端到端测试..."
    echo "-------------------"

    # 检查服务是否运行
    if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
        warn "后端服务未运行，跳过E2E测试"
        warn "请先运行: cd backend && python -m uvicorn app.main:app --reload"
        return 0
    fi

    if python tests/e2e_test.py; then
        success "端到端测试通过"
        return 0
    else
        error "端到端测试失败"
        return 1
    fi
}

# 运行前端测试（如果配置了）
run_frontend_tests() {
    echo ""
    echo "🎨 检查前端测试..."
    echo "-------------------"

    if [ -f "frontend/package.json" ]; then
        cd frontend

        if npm run test --if-present; then
            success "前端测试通过"
        else
            warn "前端测试未配置或失败"
        fi

        cd ..
    else
        warn "未找到前端项目，跳过"
    fi
}

# 运行代码质量检查
run_lint() {
    echo ""
    echo "🔍 运行代码检查..."
    echo "-------------------"

    cd backend

    # Ruff检查
    if command -v ruff &> /dev/null; then
        if ruff check app/; then
            success "Ruff 检查通过"
        else
            warn "Ruff 发现问题"
        fi
    fi

    # MyPy检查
    if command -v mypy &> /dev/null; then
        if mypy app/ --ignore-missing-imports; then
            success "MyPy 检查通过"
        else
            warn "MyPy 发现类型问题"
        fi
    fi

    cd ..
}

# 生成测试报告
generate_report() {
    echo ""
    echo "📊 测试报告"
    echo "-----------"

    if [ -d "backend/htmlcov" ]; then
        echo "覆盖率报告已生成: backend/htmlcov/index.html"
    fi
}

# 主函数
main() {
    echo "开始测试流程..."
    echo ""

    # 检查依赖
    check_dependencies

    # 运行各种测试
    FAILED=0

    run_backend_tests || FAILED=1
    run_e2e_tests || FAILED=1
    run_frontend_tests
    run_lint

    # 生成报告
    generate_report

    echo ""
    echo "========================"
    if [ $FAILED -eq 0 ]; then
        success "所有测试完成！"
        exit 0
    else
        error "部分测试失败"
        exit 1
    fi
}

# 运行主函数
main
