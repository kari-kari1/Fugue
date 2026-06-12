@echo off
REM Fugue 本地开发启动脚本（无需Docker）

echo ========================================
echo   Fugue 本地开发环境启动
echo   (无需Docker，使用SQLite数据库)
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.12+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Node.js，请先安装Node.js 20+
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

echo [信息] Python和Node.js已就绪
echo.

REM ===== 后端设置 =====
echo ========================================
echo   设置后端服务
echo ========================================
echo.

cd backend

REM 创建虚拟环境
if not exist "venv" (
    echo [步骤1] 创建Python虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo [步骤2] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [步骤3] 安装后端依赖（使用国内镜像）...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
if errorlevel 1 (
    echo [错误] 后端依赖安装失败
    pause
    exit /b 1
)

REM 创建.env文件
if not exist ".env" (
    echo [步骤4] 创建环境配置文件...
    copy .env.example .env >nul 2>&1 || (
        echo APP_NAME=Fugue > .env
        echo APP_VERSION=0.1.0 >> .env
        echo DEBUG=true >> .env
        echo DATABASE_URL=sqlite+aiosqlite:///./fugue.db >> .env
        echo SECRET_KEY=fugue-dev-secret-key-2026 >> .env
    )
)

REM 启动后端
echo [步骤5] 启动后端服务...
start "Fugue Backend" cmd /k "cd /d E:\fugue\backend && venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

cd ..

REM ===== 前端设置 =====
echo.
echo ========================================
echo   设置前端服务
echo ========================================
echo.

cd frontend

REM 安装依赖
echo [步骤6] 安装前端依赖...
if not exist "node_modules" (
    npm install
) else (
    echo [信息] node_modules已存在，跳过安装
)

if errorlevel 1 (
    echo [错误] 前端依赖安装失败
    pause
    exit /b 1
)

REM 启动前端
echo [步骤7] 启动前端服务...
start "Fugue Frontend" cmd /k "cd /d E:\fugue\frontend && npm run dev"

cd ..

REM ===== 完成 =====
echo.
echo ========================================
echo   启动完成！
echo ========================================
echo.
echo 访问地址:
echo   - 前端应用: http://localhost:3000
echo   - 后端API: http://localhost:8000
echo   - API文档: http://localhost:8000/docs
echo.
echo 数据库: SQLite (backend/fugue.db)
echo.
echo 提示: 首次访问需要注册账户
echo.
pause
