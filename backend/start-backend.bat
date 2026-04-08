@echo off
chcp 65001 >nul
echo ================================
echo   AI语音学习助手 - 后端启动
echo ================================
echo.

cd /d "%~dp0backend"

echo [1/2] 检查依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo 未安装依赖，正在安装...
    pip install -r requirements.txt
    echo.
)

echo [2/2] 启动后端服务...
echo 地址: http://localhost:9000
echo API文档: http://localhost:9000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

python -m uvicorn main:app --host 0.0.0.0 --port 9000 --reload
