@echo off
title AirMouse3D - Laptop Sensor Hub & Visualizer
echo ===================================================
echo     AirMouse 3D - Sensor Hub & Dashboard
echo ===================================================
echo Starting UDP receiver and web server...
echo.

cd /d "%~dp0"
python server.py

pause
