@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ============================================================
echo 🔧 小红书工具箱 - 安全重启服务器
echo ============================================================
echo.

rem 检查管理员权限
net session >nul 2>&1
if !errorlevel! neq 0 (
    echo ⚠️ 警告：当前不是管理员权限，可能无法强制停止进程
    echo 建议右键以管理员身份运行此脚本
    echo.
)

rem 获取当前脚本目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo 🔍 正在查找小红书工具箱服务器进程...

rem 查找特定的服务器进程（通过命令行参数识别）
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "server.py"') do (
    set "PID=%%i"
    echo 🎯 发现工具箱服务器进程: PID=!PID!
    
    echo 🛑 正在安全停止服务器进程...
    taskkill /PID !PID! /T >nul 2>&1
    if !errorlevel!==0 (
        echo ✅ 服务器进程已安全停止
    ) else (
        echo ⚠️ 无法安全停止，尝试强制停止...
        taskkill /F /PID !PID! /T >nul 2>&1
        if !errorlevel!==0 (
            echo ✅ 服务器进程已强制停止
        ) else (
            echo ❌ 无法停止服务器进程
        )
    )
)

rem 检查端口8000是否被占用
echo 🔍 检查端口8000状态...
netstat -ano | findstr ":8000 " >nul 2>&1
if !errorlevel!==0 (
    echo ⚠️ 端口8000仍被占用，尝试释放...
    for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8000 "') do (
        taskkill /F /PID %%p >nul 2>&1
    )
)

echo.
echo ⏳ 等待3秒确保进程完全停止...
timeout /t 3 /nobreak >nul

echo.
echo 🔍 验证环境依赖...
if not exist "environment\server.py" (
    echo ❌ 错误：找不到服务器文件 environment\server.py
    echo 请确保在正确的目录中运行此脚本
    pause
    exit /b 1
)

echo ✅ 环境检查通过
echo.
echo 🚀 启动新的服务器...
echo ⚠️  按 Ctrl+C 可以正确停止服务器
echo ============================================================
echo.

rem 启动服务器并捕获错误
python environment\server.py
set "EXIT_CODE=!errorlevel!"

echo.
if !EXIT_CODE!==0 (
    echo 🔚 服务器正常停止运行
) else (
    echo ❌ 服务器异常退出，退出码: !EXIT_CODE!
    echo 请检查错误信息或联系技术支持
)

echo.
echo 按任意键退出...
pause >nul 