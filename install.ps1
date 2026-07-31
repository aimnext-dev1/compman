# compman Windows One-Line Automatic Installer
$ErrorActionPreference = "Stop"

Write-Host "🚀 Installing compman CLI..." -ForegroundColor Cyan

# 1. Automatically register ~/.local/bin to User PATH & process PATH
$binDir = "$env:USERPROFILE\.local\bin"
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($userPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$binDir;$userPath", "User")
    Write-Host "✅ Automatically added '$binDir' to User PATH environment variable." -ForegroundColor Green
}

$env:PATH = "$binDir;$env:PATH"

# 2. Install compman via uv or pip
if (Get-Command uv -ErrorAction SilentlyContinue) {
    uv tool install --reinstall git+https://github.com/aimnext-dev1/compman.git
} elseif (Get-Command pip -ErrorAction SilentlyContinue) {
    pip install --upgrade git+https://github.com/aimnext-dev1/compman.git
} else {
    Write-Error "Neither 'uv' nor 'pip' was found. Please install Python or uv first."
    exit 1
}

Write-Host "`n🎉 compman installed successfully! Run 'compman --help' to get started.`n" -ForegroundColor Cyan
