@echo off
chcp 65001 >nul
title COC 跑团游戏 - 启动器

echo.
echo ================================================
echo   COC 跑团游戏 - 一键启动
echo ================================================
echo.

:: 获取脚本所在目录
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..

:: Conda 环境名称
set CONDA_ENV=python20251006

:: 切换到项目根目录
cd /d "%PROJECT_ROOT%"

echo [1/3] 启动 API 服务 (端口 5000)...
start "API服务-5000" cmd /c "cd /d %PROJECT_ROOT% && call conda activate %CONDA_ENV% && python src/front/api.py"
timeout /t 2 /nobreak >nul

echo [2/3] 启动 对话管理服务 (端口 5003)...
start "对话管理服务-5003" cmd /c "cd /d %PROJECT_ROOT% && call conda activate %CONDA_ENV% && python src/front/chat_launcher.py"
timeout /t 2 /nobreak >nul

echo [3/3] 打开游戏页面...
start "" "%SCRIPT_DIR%game.html"

echo.
echo ================================================
echo   启动完成!
echo ================================================
echo.
echo 服务列表:
echo   - API服务:       http://localhost:5000
echo   - 对话管理服务:  http://localhost:5003
echo   - AI对话服务:    通过前端"开启对话"启动
echo.
echo 按任意键关闭所有服务并退出...
pause >nul

echo.
echo 正在关闭所有服务...

:: 关闭端口 5000 的服务
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: 关闭端口 5002 的服务
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5002 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

:: 关闭端口 5003 的服务
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5003 ^| findstr LISTENING') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo 所有服务已关闭
