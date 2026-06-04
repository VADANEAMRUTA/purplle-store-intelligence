@echo off
title Purplle Store Intelligence System
color 0A

echo ========================================
echo    PURPLLE STORE INTELLIGENCE SYSTEM
echo ========================================
echo.
echo [INFO] Starting all services...
echo.

:: Kill any existing Java/Python processes
taskkill /F /IM java.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1

:: Start Spring Boot Backend
echo [1/3] Starting Spring Boot API server...
start "Purplle API" cmd /k "cd /d %~dp0spring-boot-api && mvn spring-boot:run"

:: Wait for Spring Boot to initialize
echo [WAIT] Waiting for API to start (10 seconds)...
timeout /t 10 /nobreak >nul

:: Start Dashboard Server
echo [2/3] Starting Dashboard web server...
start "Purplle Dashboard" cmd /k "cd /d %~dp0dashboard && python -m http.server 8000"

:: Optional: Start Python Tracker (uncomment if needed)
:: echo [3/3] Starting Python Tracker...
:: start "Purplle Tracker" cmd /k "cd /d %~dp0python-tracker && python app.py"

echo.
echo ========================================
echo    SYSTEM READY!
echo ========================================
echo.
echo 📊 Dashboard Access:
echo    http://localhost:8000/login.html
echo.
echo 🔌 API Endpoints:
echo    Health: http://localhost:8080/api/health
echo    Manager: http://localhost:8080/api/dashboard/manager
echo    Owner: http://localhost:8080/api/dashboard/owner
echo.
echo 👥 Available Roles:
echo    - Store Manager (Full analytics)
echo    - Store Owner (Strategic view)
echo    - Security Team (Surveillance)
echo    - Marketing Team (Campaigns)
echo.
echo 💡 Tip: Login with any role to see REAL data from your database
echo.
echo [PRESS CTRL+C TO STOP ALL SERVICES]
echo.

:: Keep window open
pause >nul
