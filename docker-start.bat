@echo off
setlocal enabledelayedexpansion

REM ============================================
REM Fugue Docker Startup Script (Windows)
REM ============================================

echo.
echo ========================================
echo   Fugue Docker Startup Script
echo ========================================
echo.

REM Check parameters
set "command=%~1"
if "%command%"=="" set "command=start"

REM Execute command
if "%command%"=="start" goto :start
if "%command%"=="stop" goto :stop
if "%command%"=="restart" goto :restart
if "%command%"=="status" goto :status
if "%command%"=="logs" goto :logs
if "%command%"=="help" goto :help
echo [ERROR] Unknown command: %command%
goto :help

:start
echo.
echo [INFO] Starting services...
echo.

REM Check .env file
if not exist ".env" (
    if exist ".env.example" (
        echo [WARN] .env file not found, creating from template...
        copy .env.example .env
        echo [INFO] Please edit .env file to configure your settings
    )
)

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads

REM Start services
echo [INFO] Starting development environment...
docker compose --profile development up -d --build

echo.
echo [INFO] Waiting for services to start (30 seconds)...
timeout /t 30 /nobreak >nul

REM Initialize data
echo.
echo [INFO] Initializing database...
docker compose exec backend alembic upgrade head
docker compose exec backend python init_data.py

REM Show status
call :show_status
goto :end

:stop
echo.
echo [INFO] Stopping services...
docker compose down
echo [OK] Services stopped
goto :end

:restart
call :stop
timeout /t 3 /nobreak >nul
goto :start

:status
call :show_status
goto :end

:logs
set "service=%~2"
if "%service%"=="" set "service=backend"
echo.
echo [INFO] Showing %service% logs (Ctrl+C to exit)...
docker compose logs -f %service%
goto :end

:show_status
echo.
echo ========================================
echo   Service Status
echo ========================================
docker compose ps
echo.
echo ========================================
echo   Access URLs
echo ========================================
echo   Frontend:    http://localhost:3000
echo   Backend API: http://localhost:8000
echo   API Docs:    http://localhost:8000/docs
echo   MinIO:       http://localhost:9001
echo.
echo ========================================
echo   Demo Account
echo ========================================
echo   Email:    demo@fugue.com
echo   Password: Demo123456
echo.
goto :eof

:help
echo.
echo Usage: docker-start.bat [command]
echo.
echo Commands:
echo   start           Start all services (default)
echo   stop            Stop all services
echo   restart         Restart all services
echo   status          Show service status
echo   logs [service]  Show service logs (default: backend)
echo   help            Show this help message
echo.
echo Examples:
echo   docker-start.bat start
echo   docker-start.bat stop
echo   docker-start.bat logs backend
echo   docker-start.bat status
echo.
goto :end

:end
endlocal
