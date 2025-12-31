@echo off
chcp 65001 >nul
title COC Game Launcher (FastAPI)

echo.
echo ================================================
echo   COC Game - Launcher (FastAPI + Uvicorn)
echo ================================================
echo.

:: Get script directory
set SCRIPT_DIR=%~dp0

:: Get project root absolute path
pushd "%SCRIPT_DIR%.."
set PROJECT_ROOT=%CD%
popd

:: Conda environment name
set CONDA_ENV=python20251006

:: Change to project root
cd /d "%PROJECT_ROOT%"

:: Check and close occupied ports
echo [0/3] Checking port usage...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5780 ^| findstr LISTENING 2^>nul') do (
    echo   Closing port 5780...
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5770 ^| findstr LISTENING 2^>nul') do (
    echo   Closing port 5770...
    taskkill /PID %%a /F >nul 2>&1
)

timeout /t 1 /nobreak >nul

echo [1/3] Starting backend service (FastAPI - port 5780)...
start "Backend-5780" cmd /k "cd /d %PROJECT_ROOT% && call conda activate %CONDA_ENV% && python -m src_test.adapter.api.main || pause"
timeout /t 3 /nobreak >nul

echo [2/3] Starting frontend service (HTTP - port 5770)...
start "Frontend-5770" cmd /c "cd /d %SCRIPT_DIR%/front && python -m http.server 5770"
timeout /t 2 /nobreak >nul

echo [3/3] Opening game page...
start "" "http://localhost:5770/game.html"

echo.
echo ================================================
echo   Startup complete!
echo ================================================
echo.
echo Services:
echo   - Backend (FastAPI):  http://localhost:5780
echo   - Frontend (HTTP):    http://localhost:5770
echo   - API Docs:           http://localhost:5780/docs
echo.
echo Press any key to close all services and exit...
pause >nul

echo.
echo Closing all services...

:: Close port processes
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5780 ^| findstr LISTENING 2^>nul') do (
    echo   Closing port 5780 (backend)
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5770 ^| findstr LISTENING 2^>nul') do (
    echo   Closing port 5770 (frontend)
    taskkill /PID %%a /F >nul 2>&1
)

:: Close cmd windows
taskkill /FI "WINDOWTITLE eq Backend-5780" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend-5770" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Backend-5780 - cmd*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Frontend-5770 - cmd*" /F >nul 2>&1

timeout /t 1 /nobreak >nul

:: Check and close remaining ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5780 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5770 ^| findstr LISTENING 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo All services closed
timeout /t 2 /nobreak >nul
