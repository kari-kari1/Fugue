#!/bin/bash
# Fugue 开发环境启动脚本 (Linux/macOS)

set -e

echo "========================================"
echo "  Fugue - 多智能体协作工作流平台"
echo "  开发环境启动脚本"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查依赖
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}[错误] 未找到 $1${NC}"
        return 1
    fi
    return 0
}

echo "检查系统依赖..."

# 检查Python
if ! check_command python3; then
    echo "请先安装Python 3.12+"
    exit 1
fi

# 检查Node.js
if ! check_command node; then
    echo "请先安装Node.js 20+"
    exit 1
fi

# 检查npm
if ! check_command npm; then
    echo "请先安装npm"
    exit 1
fi

# 检查Docker（可选）
USE_DOCKER=false
if check_command docker; then
    if check_command docker-compose; then
        USE_DOCKER=true
        echo -e "${GREEN}[✓] 检测到Docker${NC}"
    fi
fi

echo ""
echo "请选择启动方式:"
echo "1. 使用Docker Compose启动（推荐）"
echo "2. 本地启动"
echo "3. 仅启动前端"
echo "4. 仅启动后端"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        if [ "$USE_DOCKER" = false ]; then
            echo -e "${RED}[错误] 未安装Docker，无法使用此选项${NC}"
            exit 1
        fi

        echo ""
        echo -e "${GREEN}[步骤1] 启动Docker Compose服务...${NC}"
        docker-compose up -d

        echo ""
        echo -e "${GREEN}[完成] 所有服务已启动！${NC}"
        echo ""
        echo "访问地址:"
        echo "  - 前端: http://localhost:3000"
        echo "  - 后端API: http://localhost:8000"
        echo "  - API文档: http://localhost:8000/docs"
        echo "  - MinIO控制台: http://localhost:9001"
        echo ""
        echo "查看日志: docker-compose logs -f"
        echo "停止服务: docker-compose down"
        ;;

    2)
        echo ""
        echo -e "${YELLOW}[信息] 请确保以下服务已启动:${NC}"
        echo "  - PostgreSQL (端口5432)"
        echo "  - Redis (端口6379)"
        echo ""
        echo "PostgreSQL配置:"
        echo "  - 数据库: fugue"
        echo "  - 用户: postgres"
        echo "  - 密码: postgres"
        echo ""

        # 创建数据库
        echo -e "${GREEN}[步骤1] 创建数据库...${NC}"
        PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE fugue;" 2>/dev/null || echo "数据库已存在或创建失败（可忽略）"

        # 安装后端依赖
        echo ""
        echo -e "${GREEN}[步骤2] 安装后端依赖...${NC}"
        cd backend
        pip install -r requirements.txt

        # 运行数据库迁移
        echo ""
        echo -e "${GREEN}[步骤3] 运行数据库迁移...${NC}"
        alembic upgrade head 2>/dev/null || {
            echo "创建初始迁移..."
            alembic revision --autogenerate -m "Initial migration"
            alembic upgrade head
        }

        # 安装前端依赖
        echo ""
        echo -e "${GREEN}[步骤4] 安装前端依赖...${NC}"
        cd ../frontend
        npm install

        # 启动后端
        echo ""
        echo -e "${GREEN}[步骤5] 启动后端服务...${NC}"
        cd ../backend
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
        BACKEND_PID=$!

        # 启动前端
        echo ""
        echo -e "${GREEN}[步骤6] 启动前端服务...${NC}"
        cd ../frontend
        npm run dev &
        FRONTEND_PID=$!

        echo ""
        echo -e "${GREEN}[完成] 开发服务器已启动！${NC}"
        echo ""
        echo "访问地址:"
        echo "  - 前端: http://localhost:3000"
        echo "  - 后端API: http://localhost:8000"
        echo "  - API文档: http://localhost:8000/docs"
        echo ""
        echo "按 Ctrl+C 停止所有服务"

        # 等待信号
        trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
        wait
        ;;

    3)
        echo ""
        echo -e "${GREEN}[步骤1] 安装前端依赖...${NC}"
        cd frontend
        npm install

        echo ""
        echo -e "${GREEN}[步骤2] 启动前端开发服务器...${NC}"
        npm run dev
        ;;

    4)
        echo ""
        echo -e "${GREEN}[步骤1] 安装后端依赖...${NC}"
        cd backend
        pip install -r requirements.txt

        echo ""
        echo -e "${GREEN}[步骤2] 启动后端开发服务器...${NC}"
        uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
        ;;

    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac
