@echo off
chcp 65001 > nul
echo [compman] Installing compman CLI...

:: Remove old pip-installed compman from Python Scripts directories (prevents PATH conflicts)
for %%D in (
    "%USERPROFILE%\AppData\Local\Programs\Python\Python314\Scripts\compman.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python313\Scripts\compman.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python312\Scripts\compman.exe"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python311\Scripts\compman.exe"
    "%USERPROFILE%\AppData\Roaming\Python\Scripts\compman.exe"
) do (
    if exist %%D (
        del /f /q %%D 2>nul
        echo [compman] Removed old compman: %%D
    )
)

:: Run PowerShell installer with cache-busting timestamp to always fetch the latest version
for /f %%T in ('powershell -NoProfile -Command "[int](Get-Date -UFormat %%s)"') do set TS=%%T
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://raw.githubusercontent.com/aimnext-dev1/compman/main/install.ps1?t=%TS%' | iex"

if %ERRORLEVEL% NEQ 0 (
    echo Error: Installation failed.
    exit /b %ERRORLEVEL%
)

:: Apply .local\bin to current CMD session PATH immediately
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

echo.
echo [compman] Installation complete!
echo [compman] NOTE: Open a NEW cmd/terminal window for compman to be found automatically.
