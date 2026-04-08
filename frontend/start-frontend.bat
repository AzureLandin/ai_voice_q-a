@echo off
chcp 65001 >nul
echo ================================
echo   AI语音学习助手 - 前端启动
echo ================================
echo.

cd /d "%~dp0frontend"

echo 启动前端服务...
echo 地址: http://localhost:8080
echo.
echo 按 Ctrl+C 停止服务
echo.

python -m http.server 8080
