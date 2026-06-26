@echo off
title CES IND Transport Roster
cls
echo =========================================================
echo   CES IND Transport Roster - Startup
echo =========================================================
echo.

:: Project root is where this script lives
set "PROJECT_ROOT=%~dp0"
set "VENV_DIR=%LOCALAPPDATA%\transport_roster_venv"
set "APP_DIR=%PROJECT_ROOT%app"
set "PYPI_URL=https://pypi.ci.artifacts.walmart.com/artifactory/api/pypi/external-pypi/simple"
set "PYPI_HOST=pypi.ci.artifacts.walmart.com"
set "PORT=8501"

echo Project root : %PROJECT_ROOT%
echo Venv         : %VENV_DIR%
echo App port     : http://127.0.0.1:%PORT%
echo.

:: ---- Create venv if missing ----
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo [1/4] Creating virtual environment...
    uv venv "%VENV_DIR%" 2>nul || python -m venv "%VENV_DIR%"
    echo       Done.
) else (
    echo [1/4] Virtual environment already exists. Skipping.
)

:: ---- Install / upgrade dependencies ----
echo [2/4] Installing dependencies...
uv pip install --python "%VENV_DIR%\Scripts\python.exe" ^
    --index-url %PYPI_URL% ^
    --allow-insecure-host %PYPI_HOST% ^
    --link-mode=copy ^
    -r "%PROJECT_ROOT%requirements.txt"

if errorlevel 1 (
    echo.
    echo ERROR: Dependency install failed. Check VPN / Walmart network.
    pause
    exit /b 1
)
echo       Done.

:: ---- GCP credentials check ----
echo [3/4] Checking GCP credentials...
if defined GOOGLE_APPLICATION_CREDENTIALS (
    echo       Service account key found: %GOOGLE_APPLICATION_CREDENTIALS%
) else (
    echo       No service account key set.
    echo       Using Application Default Credentials (gcloud auth).
    echo       If refresh fails, run: gcloud auth application-default login
)
echo.

:: ---- Launch server ----
echo [4/4] Starting server on http://127.0.0.1:%PORT% ...
echo       Press Ctrl+C to stop.
echo.

:: Open browser after 3 seconds
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:%PORT%"

:: Run the app
"%VENV_DIR%\Scripts\python.exe" "%APP_DIR%\main.py"

echo.
echo Server stopped.
pause
