@echo off
echo ============================================================
echo           Launching MockForge AI Platform...
echo ============================================================
echo.

echo 1. Starting FastAPI Backend Engine on http://127.0.0.1:8000 ...
start "MockForge Backend" cmd /k "cd backend && py -m uvicorn app.main:app --port 8000 --reload"

echo 2. Starting React + Vite Web Dashboard on http://localhost:3000 ...
start "MockForge Dashboard" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================================
echo MockForge AI is running!
echo Dashboard UI: http://localhost:3000
echo Backend API:  http://127.0.0.1:8000
echo ============================================================
