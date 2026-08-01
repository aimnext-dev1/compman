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

:: Download install.ps1 to temp with cache-busting header, then execute locally
curl -fsSL -H "Cache-Control: no-cache" https://raw.githubusercontent.com/allbegray/compman/main/install.ps1 -o "%TEMP%\compman_install.ps1"
if %ERRORLEVEL% NEQ 0 (
    echo Error: Failed to download install.ps1.
    exit /b %ERRORLEVEL%
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%TEMP%\compman_install.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo Error: Installation failed.
    exit /b %ERRORLEVEL%
)

:: Apply .local\bin to current CMD session PATH immediately
set "PATH=%USERPROFILE%\.local\bin;%PATH%"

echo.
echo [compman] Installation complete!
echo [compman] NOTE: Open a NEW cmd/terminal window for compman to be found automatically.
