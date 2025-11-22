Write-Host "`n[1/3] Cleaning up old environment..." -ForegroundColor Cyan

if (Test-Path "backend\.venv") {
    Write-Host "Removing backend virtual environment..." -ForegroundColor DarkYellow
    Remove-Item -Recurse -Force "backend\.venv"
}

if (Test-Path "backend\__pycache__") {
    Write-Host "Removing Python cache..." -ForegroundColor DarkYellow
    Remove-Item -Recurse -Force "backend\__pycache__"
}

if (Test-Path "frontend\node_modules") {
    Write-Host "Removing old node_modules..." -ForegroundColor DarkYellow
    Remove-Item -Recurse -Force "frontend\node_modules"
}

if (Test-Path "frontend\package-lock.json") {
    Write-Host "Removing old package-lock.json..." -ForegroundColor DarkYellow
    Remove-Item -Force "frontend\package-lock.json"
}


Write-Host "`n[2/3] Setting up backend environment..." -ForegroundColor Cyan

Set-Location backend
python -m venv .venv
. .\.venv\Scripts\Activate.ps1

Write-Host "Upgrading pip and installing requirements..." -ForegroundColor DarkYellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install Python dependencies." -ForegroundColor Red
    pause
    exit 1
}

deactivate
Set-Location ..


Write-Host "`n[3/3] Setting up frontend environment..." -ForegroundColor Cyan

Set-Location frontend

Write-Host "Installing npm dependencies..." -ForegroundColor DarkYellow
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to install frontend dependencies." -ForegroundColor Red
    pause
    exit 1
}

Set-Location ..

Write-Host "`nSetup complete!" -ForegroundColor Green
Write-Host "`nTo start the project, run the start script :)" -ForegroundColor Magenta
pause
