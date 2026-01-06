@echo off
chcp 65001 >nul
title COC Game Launcher

echo.
echo ================================================
echo   COC Game - 一键启动
echo ================================================
echo.

:: Get script directory (project root)
set SCRIPT_DIR=%~dp0

:: Change to project root
cd /d "%SCRIPT_DIR%"

:: Check if venv exists
if not exist venv (
    echo [错误] 虚拟环境不存在！
    echo.
    echo 请先运行 setup_venv.bat 安装环境
    echo.
    pause
    exit /b 1
)

:: Activate venv
echo [0/4] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)

:: Check and close occupied ports
echo [1/4] 检查端口占用...

:: 清理5780端口（后端）
echo   正在清理端口 5780...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5780" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a
)

:: 清理5770端口（前端）
echo   正在清理端口 5770...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5770" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a
)

echo   端口清理完成

:: 等待端口完全释放
timeout /t 2 /nobreak >nul

:: Start backend service
echo [2/4] 启动后端服务 (FastAPI - 端口 5780)...
start "Backend-5780" cmd /k "cd /d %SCRIPT_DIR% && call venv\Scripts\activate.bat && python -m src_test.adapter.api.main"
timeout /t 3 /nobreak >nul

:: Start frontend service
echo [3/4] 启动前端服务 (HTTP - 端口 5770)...
start "Frontend-5770" cmd /c "cd /d %SCRIPT_DIR%\src_test\front && call ..\..\venv\Scripts\activate.bat && python -m http.server 5770"
timeout /t 2 /nobreak >nul

:: Open browser
echo [4/4] 打开游戏页面...
start "" "http://localhost:5770/game.html"

echo.
echo ================================================
echo   启动完成！
echo ================================================
echo.
echo 服务地址:
echo   - 后端 (FastAPI):  http://localhost:5780
echo   - 前端 (HTTP):     http://localhost:5770
echo   - API 文档:        http://localhost:5780/docs
echo.
echo 按任意键关闭所有服务并退出...
pause >nul

echo.
echo 正在关闭所有服务...

:: Close port processes
echo   正在关闭端口 5780 (后端)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5780" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a
)

echo   正在关闭端口 5770 (前端)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5770" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a
)

:: Close cmd windows by command line
echo   正在关闭命令行窗口...

:: 使用wmic查找包含特定标题的cmd进程并关闭
for /f "tokens=2" %%p in ('wmic process where "name='cmd.exe' and commandline like '%%Backend-5780%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    echo   找到后端窗口 PID: %%p，正在关闭...
    taskkill /F /PID %%p >nul 2>&1
)
for /f "tokens=2" %%p in ('wmic process where "name='cmd.exe' and commandline like '%%Frontend-5770%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    echo   找到前端窗口 PID: %%p，正在关闭...
    taskkill /F /PID %%p >nul 2>&1
)

:: 等待进程完全关闭
timeout /t 1 /nobreak >nul

:: Check and close remaining ports (二次确认)
echo   确认端口已释放...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5780" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5770" ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%a
)

echo.
echo 所有服务已关闭
timeout /t 1 /nobreak >nul
