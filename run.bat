@echo off
cd /d "%~dp0"
echo Starting BizGuard AI...
echo.
"..\bizguard-venv\Scripts\streamlit.exe" run app.py --server.port 8599
pause
