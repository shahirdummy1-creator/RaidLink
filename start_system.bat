@echo off
echo Starting RaidLink Taxi Booking System...
echo.

echo [1/3] Starting Flask application...
start /B python App.py
timeout /t 3 /nobreak >nul

echo [2/3] Waiting for server to start...
timeout /t 5 /nobreak >nul

echo [3/3] Testing booking distribution system...
python test_booking_system.py

echo.
echo System is ready! 
echo - Driver login: http://localhost:7860/driver-login
echo - Rider login: http://localhost:7860/rider-login  
echo - Admin login: http://localhost:7860/admin-login
echo.
pause