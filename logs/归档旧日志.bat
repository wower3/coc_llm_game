@echo off
setlocal enabledelayedexpansion

echo ========================================
echo       Log Archive Script (Pure BAT)
echo ========================================
echo.

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 获取今天的日期
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "DATETIME=%%I"
set "TODAY=%DATETIME:~0,8%"

echo Today: %TODAY%
echo Archiving logs from before today...
echo.

REM 创建history目录
if not exist "history" mkdir "history"

REM 查找需要归档的文件夹
set "COUNT=0"
for /d %%D in (*) do (
    set "FOLDER_NAME=%%~nxD"
    set "FOLDER_DATE=!FOLDER_NAME:~0,8!"
    
    REM 检查是否匹配日志文件夹格式（8位数字开头）
    REM 注意：使用 set /p 避免 echo 添加尾随空格导致 $ 锚点匹配失败
    <nul set /p="!FOLDER_DATE!" | findstr /r /c:"^[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]$" >nul
    if !errorlevel! EQU 0 (
        REM 只归档今天之前的日志
        if !FOLDER_DATE! LSS %TODAY% (
            set /a "COUNT+=1"
            set "FOLDER_!COUNT!=%%D"
            echo   - !FOLDER_NAME! (!FOLDER_DATE!)
        )
    )
)

echo.
echo Found !COUNT! folders to archive
echo.

if !COUNT! EQU 0 (
    echo No log folders found to archive
    pause
    exit /b 0
)

echo Starting archive...
echo.

REM 归档处理
set "SUCCESS=0"
set "FAILED=0"

for /l %%i in (1,1,!COUNT!) do (
    set "TARGET_FOLDER=!FOLDER_%%i!"
    for %%F in ("!TARGET_FOLDER!") do set "FOLDER_NAME=%%~nxF"
    set "FOLDER_DATE=!FOLDER_NAME:~0,8!"
    
    REM 创建按日期分类的目录
    set "HISTORY_DIR=history\!FOLDER_DATE!"
    if not exist "!HISTORY_DIR!" mkdir "!HISTORY_DIR!"
    
    REM 压缩为zip文件
    set "ZIP_FILE=!HISTORY_DIR!\!FOLDER_NAME!.zip"
    
    echo Compressing: !FOLDER_NAME!
    call :ZipFolder "!TARGET_FOLDER!" "!ZIP_FILE!"
    
    if exist "!ZIP_FILE!" (
        REM 检查zip文件大小，确保不是空文件
        for %%A in ("!ZIP_FILE!") do set "ZIP_SIZE=%%~zA"
        if !ZIP_SIZE! GTR 100 (
            REM 删除源文件夹
            rd /s /q "!TARGET_FOLDER!"
            echo   Done - Created zip
            set /a "SUCCESS+=1"
        ) else (
            echo   Failed - Invalid zip file
            set /a "FAILED+=1"
        )
    ) else (
        echo   Failed - Zip not created
        set /a "FAILED+=1"
    )
)

echo.
echo ========================================
echo       Archive Complete!
echo ========================================
echo.
echo Statistics:
echo   Success: !SUCCESS! folders
echo   Failed: !FAILED! folders
echo.
echo History logs saved in: history\
echo.

pause
goto :EOF

REM ========== ZIP 压缩子程序 ==========
:ZipFolder
set "SOURCE=%~1"
set "TARGET=%~2"

REM 使用 PowerShell Compress-Archive 进行压缩
powershell -NoProfile -Command "Compress-Archive -Path '%SOURCE%\*' -DestinationPath '%TARGET%' -Force" >nul 2>&1

goto :EOF
