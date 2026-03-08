# Start the bigdata pipeline (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  Bigdata Pipeline - Starting All Services" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

Push-Location "$PSScriptRoot\.."

try {
    Write-Host "`n[1/3] Building custom images..." -ForegroundColor Yellow
    docker compose build

    Write-Host "[2/3] Starting all services..." -ForegroundColor Yellow
    docker compose up -d

    Write-Host "[3/3] Waiting for services to be healthy..." -ForegroundColor Yellow

    $services = @("zookeeper", "kafka", "namenode", "elasticsearch")
    foreach ($svc in $services) {
        Write-Host "  Waiting for $($svc.PadRight(20))" -NoNewline
        do {
            Start-Sleep -Seconds 2
            $status = docker compose ps $svc 2>&1
        } while ($status -notmatch "healthy")
        Write-Host "ready" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "  All services are up!" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Kafka:          localhost:9092"
    Write-Host "  HDFS Namenode:  http://localhost:9870"
    Write-Host "  Spark UI:       http://localhost:8080"
    Write-Host "  Elasticsearch:  http://localhost:9200"
    Write-Host "  Kibana:         http://localhost:5601"
    Write-Host "  Hive Server:    localhost:10000"
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  View logs: docker compose logs -f"
    Write-Host "  Stop:      docker compose down"
    Write-Host "==========================================" -ForegroundColor Green
}
finally {
    Pop-Location
}
