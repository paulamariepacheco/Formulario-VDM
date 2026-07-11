@echo off
cd /d "%~dp0"
python gerar.py
if errorlevel 1 pause
