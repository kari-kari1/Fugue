@echo off
REM Fugue 开发环境启动脚本 (Windows)

echo ========================================
echo   Fugue - 多智能体协作工作流平台
echo   开发环境启动脚本
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.12+
    pause
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Node.js，请先安装Node.js 20+
    pause
    exit /b 1
)

REM 检查Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [警告] 未找到Docker，将使用本地服务
    set USE_DOCKER=false
) else (
    echo [信息] 检测到Docker，可以选择使用Docker启动
    set USE_DOCKER=true
)

echo.
echo 请选择启动方式:
echo 1. 使用Docker Compose启动（推荐，自动启动所有服务）
echo 2. 本地启动（需要手动启动PostgreSQL和Redis）
echo 3. 仅启动前端开发服务器
echo 4. 仅启动后端开发服务器
echo.
set /p choice="请输入选项 (1-4): "

if "%choice%"=="1" goto docker_start
if "%choice%"=="2" goto local_start
if "%choice%"=="3" goto frontend_only
if "%choice%"=="4" goto backend_only
echo 无效选项
pause
exit /b 1

:docker_start
echo.
echo [步骤1] 启动Docker Compose服务...
docker compose up -d
echo.
echo [完成] 所有服务已启动！
echo.
echo 访问地址:
echo   - 前端: http://localhost:3000
echo   - 后端API: http://localhost:8000
echo   - API文档: http://localhost:8000/docs
echo   - MinIO控制台: http://localhost:9001
echo.
echo 按任意键查看日志...
pause >nul
docker compose logs -f
goto end

:local_start
echo.
echo [步骤1] 启动PostgreSQL和Redis...
echo 请确保PostgreSQL和Redis已启动并运行
echo.
echo PostgreSQL配置:
echo   - 数据库: fugue
echo   - 用户: postgres
echo   - 密码: postgres
echo   - 端口: 5432
echo.
echo Redis配置:
echo   - 端口: 6379
echo.

echo [步骤2] 安装后端依赖...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 后端依赖安装失败
    pause
    exit /b 1
)

echo.
echo [步骤3] 创建数据库...
psql -U postgres -c "CREATE DATABASE fugue;" 2>nul
echo 数据库创建完成（如果已存在则忽略）

echo.
echo [步骤4] 运行数据库迁移...
alembic upgrade head
if errorlevel 1 (
    echo [警告] 迁移失败，尝试创建初始迁移...
    alembic revision --autogenerate -m "Initial migration"
    alembic upgrade head
)

echo.
echo [步骤5] 安装前端依赖...
cd ..\frontend
npm install
if errorlevel 1 (
    echo [错误] 前端依赖安装失败
    pause
    exit /b 1
)

echo.
echo [步骤6] 启动后端服务...
cd ..\backend
start "Fugue Backend" cmd /k "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo [步骤7] 启动前端服务...
cd ..\frontend
start "Fugue Frontend" cmd /k "npm run dev"

echo.
echo [完成] 开发服务器已启动！
echo.
echo 访问地址:
echo   - 前端: http://localhost:3000
echo   - 后端API: http://localhost:8000
echo   - API文档: http://localhost:8000/docs
echo.
pause
goto end

:frontend_only
echo.
echo [步骤1] 安装前端依赖...
cd frontend
npm install
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [步骤2] 启动前端开发服务器...
npm run dev
goto end

:backend_only
echo.
echo [步骤1] 安装后端依赖...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [步骤2] 启动后端开发服务器...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
goto end

:end
