@echo off
cd /d "%~dp0"
echo Starting BizGuard AI...
echo.
"..\bizguard-venv\Scripts\python.exe" -m streamlit run app.py --server.port 8600
pause
