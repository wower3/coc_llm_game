@echo off
chcp 65001 >nul
title COC 跑团游戏 - 启动器 (FastAPI)

echo.
echo ================================================
echo   COC 跑团游戏 - 一键启动 (FastAPI + Uvicorn)
echo ================================================
echo.

:: 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..

:: Conda 环境名称
set CONDA_ENV=python20251006

:: 切换到项目根目录
cd /d "%PROJECT_ROOT%"

:: 检测并关闭已占用的端口
echo [0/4] 检测端口占用情况...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5780 ^| findstr LISTENING 2^>nul') do (
    echo   关闭端口 5780...
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5782 ^| findstr LISTENING 2^>nul') do (
    echo   关闭端口 5782...
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5781 ^| findstr LISTENING 2^>nul') do (
    echo   关闭端口 5781...
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5770 ^| findstr LISTENING 2^>nul') do (
    echo   关闭端口 5770...
    taskkill /PID %%a /F >nul 2>&1
)

timeout /t 1 /nobreak >nul

echo [1/4] 启动 API 服务 (FastAPI - 端口 5780)...
start "API服务-5780" cmd /c "cd /d %PROJECT_ROOT% && call conda activate %CONDA_ENV% && python src/front/api.py"
timeout /t 2 /nobreak >nul

echo [2/4] 启动 对话管理服务 (FastAPI - 端口 5781)...
start "对话管理服务-5781" cmd /c "cd /d %PROJECT_ROOT% && call conda activate %CONDA_ENV% && python src/front/chat_launcher.py"
timeout /t 2 /nobreak >nul

echo [3/4] 启动前端服务 (HTTP - 端口 5770)...
start "前端服务-5770" cmd /c "cd /d %SCRIPT_DIR% && python -m http.server 5770"
timeout /t 2 /nobreak >nul

echo [4/4] 打开游戏页面...
start "" "http://localhost:5770/game.html"

echo.
echo ================================================
echo   启动完成! (FastAPI + Uvicorn)
echo ================================================
echo.
echo 服务列表:
echo   - API服务 (FastAPI):      http://localhost:5780
echo   - 对话管理服务 (FastAPI): http://localhost:5781
echo   - AI对话服务 (FastAPI):   通过前端"开启对话"启动 (端口5782)
echo   - 前端服务 (HTTP):        http://localhost:5770
echo.
echo 按任意键关闭所有服务并退出...
pause >nul

echo.
echo 正在关闭所有服务...

:: 先关闭端口对应的Python进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5780 ^| findstr LISTENING 2^>nul') do (
    echo   关闭端口 5780 (API服务)
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5782 ^| findstr LISTENING 2^>nul') do (
    echo   关闭端口 5782 (AI对话服务)
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5781 ^| findstr LISTENING 2^>nul') do (
    echo   关闭端口 5781 (对话管理服务)
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5770 ^| findstr LISTENING 2^>nul') do (
    echo   关闭端口 5770 (前端服务)
    taskkill /PID %%a /F >nul 2>&1
)

:: 关闭对应的cmd窗口
taskkill /FI "WINDOWTITLE eq API服务-5780" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 对话管理服务-5781" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 前端服务-5770" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq API服务-5780 - cmd*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 对话管理服务-5781 - cmd*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq 前端服务-5770 - cmd*" /F >nul 2>&1

timeout /t 1 /nobreak >nul

:: 再次检查并关闭残留端口
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5780 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5782 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5781 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5770 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo 所有服务已关闭
timeout /t 2 /nobreak >nul
