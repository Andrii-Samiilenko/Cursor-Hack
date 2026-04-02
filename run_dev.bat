@echo off
cd /d "%~dp0"
python run_dev.py
if errorlevel 1 pause
