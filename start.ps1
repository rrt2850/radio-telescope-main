Write-Host "`n[1/2] Starting backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend/.venv/Scripts; ./Activate.ps1; cd ../..; uvicorn main:app --reload
"

Write-Host "`n[2/2] Starting frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`nAll services started in separate windows." -ForegroundColor Green
Write-Host "Backend: http://127.0.0.1:8000 " -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Yellow
pause
