@echo off
chcp 65001 >nul
echo ================================
echo   AI语音学习助手 - 一键启动
echo ================================
echo.

cd /d "%~dp0"

echo [1/3] 启动后端...
start "AI语音助手-后端" cmd /k "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 3 >nul

echo [2/3] 启动前端...
start "AI语音助手-前端" cmd /k "cd frontend && python -m http.server 8080"
timeout /t 2 >nul

echo [3/3] 打开浏览器...
start http://localhost:8080

echo.
echo ================================
echo   启动完成！
echo   后端: http://localhost:8000
echo   前端: http://localhost:8080
echo ================================
echo.
echo 提示: 关闭两个命令行窗口即可停止服务
