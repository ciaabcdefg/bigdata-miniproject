# Stop the bigdata pipeline and clean up (PowerShell)
Write-Host "Stopping all services..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\.."
try {
    docker compose down -v
    Write-Host "All services stopped and volumes removed." -ForegroundColor Green
}
finally {
    Pop-Location
}
