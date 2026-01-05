@echo off
chcp 65001 >nul
title COC Game - 环境安装/更新

echo.
echo ================================================
echo   COC Game - 虚拟环境安装/更新
echo ================================================
echo.
echo 此脚本将：
echo   1. 创建虚拟环境（如果不存在）
echo   2. 检查并安装/更新所有依赖
echo.

:: Get script directory (project root)
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] 检查虚拟环境...
if exist venv (
    echo 虚拟环境已存在
) else (
    echo 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功
)

echo.
echo [2/4] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)

echo.
echo [3/4] 升级 pip...
python -m pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [4/4] 安装/更新项目依赖...
echo.
echo 正在检查并安装以下包：
echo   - langchain (AI框架)
echo   - fastapi (Web框架)
echo   - PyMySQL (数据库)
echo   - cryptography (MySQL加密连接)
echo   - loguru (日志)
echo   - PyJWT (认证)
echo   - 其他依赖...
echo.

pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo ================================================
echo   安装/更新完成！
echo ================================================
echo.
echo 虚拟环境位置: %SCRIPT_DIR%venv
echo.
echo 现在可以运行 start.bat 启动游戏
echo.
pause
