@echo off
chcp 65001 > nul
echo [compman] Installing compman CLI...

powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/aimnext-dev1/compman/main/install.ps1 | iex"

if %ERRORLEVEL% NEQ 0 (
    echo Error: Installation failed.
    exit /b %ERRORLEVEL%
)

set "PATH=%USERPROFILE%\.local\bin;%PATH%"

echo [compman] Installation complete!
