# compman Windows One-Line Automatic Installer
$ErrorActionPreference = "Continue"

Write-Host "🚀 Installing compman CLI..." -ForegroundColor Cyan

# 1. Remove old pip-installed compman from any Python Scripts directory (prevents PATH conflicts)
$oldPipPaths = @(
    "$env:USERPROFILE\AppData\Local\Programs\Python\Python314\Scripts\compman.exe",
    "$env:USERPROFILE\AppData\Local\Programs\Python\Python313\Scripts\compman.exe",
    "$env:USERPROFILE\AppData\Local\Programs\Python\Python312\Scripts\compman.exe",
    "$env:USERPROFILE\AppData\Local\Programs\Python\Python311\Scripts\compman.exe",
    "$env:USERPROFILE\AppData\Roaming\Python\Scripts\compman.exe"
)
foreach ($p in $oldPipPaths) {
    if (Test-Path $p) {
        Remove-Item $p -Force -ErrorAction SilentlyContinue
        Write-Host "🧹 Removed old pip-installed compman from: $p" -ForegroundColor Yellow
    }
}

# 2. Ensure ~/.local/bin is at the FRONT of User PATH
$binDir = "$env:USERPROFILE\.local\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathParts = ($userPath -split ';') | Where-Object { $_ -ne "" -and $_ -ne $binDir }
$newUserPath = ($binDir + ";" + ($pathParts -join ";")).TrimEnd(";")
[Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
$env:PATH = "$binDir;$env:PATH"
Write-Host "✅ Ensured '$binDir' is at the front of User PATH." -ForegroundColor Green

# 3. Install compman via uv (uv manages its own Python, so older system Python is fine)
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "Installing uv (Python package manager)..." -ForegroundColor Yellow
    irm https://astral.sh/uv/install.ps1 | iex
}
# uv tool install places shims in ~/.local/bin (already set at front of PATH above)
uv tool install --reinstall --managed-python git+https://github.com/allbegray/compman.git

# 4. Automatically register PowerShell Tab auto-completion & execution policy
if (Get-Command compman -ErrorAction SilentlyContinue) {
    try {
        Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force -ErrorAction SilentlyContinue
        compman completion powershell --install | Out-Null
        Write-Host "✅ Registered shell auto-completion for PowerShell." -ForegroundColor Green
    } catch {
        # ignore if profile cannot be modified
    }
}

Write-Host "`n🎉 compman installed successfully! Run 'compman --help' to get started." -ForegroundColor Cyan
Write-Host "   ⚠️  Please open a new terminal window for the PATH changes to take effect." -ForegroundColor Yellow
