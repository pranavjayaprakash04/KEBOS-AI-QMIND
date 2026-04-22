Write-Host "🐳 Checking Docker Status..." -ForegroundColor Blue
Write-Host "==============================" -ForegroundColor Blue

$attempts = 0
$maxAttempts = 10

while ($attempts -lt $maxAttempts) {
    $attempts++
    Write-Host "[$attempts/$maxAttempts] Testing Docker..." -ForegroundColor Cyan
    
    try {
        docker version | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Docker is ready!" -ForegroundColor Green
            Write-Host ""
            
            # Clean up existing container
            Write-Host "Cleaning up existing containers..." -ForegroundColor Yellow
            docker stop kebos-postgres 2>$null
            docker rm kebos-postgres 2>$null
            
            # Start PostgreSQL
            Write-Host "Starting PostgreSQL container..." -ForegroundColor Blue
            docker run -d --name kebos-postgres --restart unless-stopped -p 5432:5432 -e POSTGRES_DB=ctp_database -e POSTGRES_USER=ctp_user -e POSTGRES_PASSWORD=secure_ctp_password_2024 postgres:13
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ PostgreSQL container started!" -ForegroundColor Green
                Write-Host ""
                Write-Host "⏳ Waiting 30 seconds for PostgreSQL to initialize..." -ForegroundColor Yellow
                Start-Sleep -Seconds 30
                
                Write-Host "📊 Container Status:" -ForegroundColor Blue
                docker ps --filter "name=kebos-postgres"
                
                Write-Host ""
                Write-Host "🎉 SETUP COMPLETE!" -ForegroundColor Green
                Write-Host "PostgreSQL is running on port 5432"
                Write-Host ""
                Write-Host "Next: Start your backend to test the connection!"
                exit 0
            } else {
                Write-Host "❌ Failed to start PostgreSQL" -ForegroundColor Red
                exit 1
            }
        }
    }
    catch {
        Write-Host "   Docker not ready, waiting 10 seconds..." -ForegroundColor Gray
        Start-Sleep -Seconds 10
    }
}

Write-Host "⏰ Docker is still starting. Please wait and try:" -ForegroundColor Yellow
Write-Host "docker --version" -ForegroundColor Gray
