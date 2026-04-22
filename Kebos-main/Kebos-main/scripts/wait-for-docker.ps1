Write-Host "🐳 Waiting for Docker Desktop to be ready..." -ForegroundColor Blue
Write-Host "=======================================" -ForegroundColor Blue

$dockerReady = $false
$attempts = 0
$maxAttempts = 20

Write-Host "Docker Desktop processes detected. Checking readiness..." -ForegroundColor Yellow
Write-Host ""

while (-not $dockerReady -and $attempts -lt $maxAttempts) {
    $attempts++
    Write-Host "[$attempts/$maxAttempts] Testing Docker..." -ForegroundColor Cyan
    
    try {
        $result = docker version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $dockerReady = $true
            Write-Host "✅ Docker is ready!" -ForegroundColor Green
            Write-Host ""
            docker version --format "Client: {{.Client.Version}}"
            docker version --format "Server: {{.Server.Version}}"
            break
        }
    }
    catch {
        # Still starting
    }
    
    if (-not $dockerReady) {
        Write-Host "   Still starting... waiting 10 seconds" -ForegroundColor Gray
        Start-Sleep -Seconds 10
    }
}

if ($dockerReady) {
    Write-Host ""
    Write-Host "🚀 Docker is ready! Starting PostgreSQL setup..." -ForegroundColor Green
    Write-Host ""
    
    # Clean up any existing container
    Write-Host "Cleaning up existing containers..." -ForegroundColor Yellow
    docker stop kebos-postgres 2>$null
    docker rm kebos-postgres 2>$null
    
    # Start PostgreSQL
    Write-Host "Starting PostgreSQL container..." -ForegroundColor Blue
    $postgresCmd = "docker run -d --name kebos-postgres --restart unless-stopped -p 5432:5432 -e POSTGRES_DB=ctp_database -e POSTGRES_USER=ctp_user -e POSTGRES_PASSWORD=secure_ctp_password_2024 -v kebos_postgres_data:/var/lib/postgresql/data postgres:13"
    
    Invoke-Expression $postgresCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ PostgreSQL container started!" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "⏳ Waiting for PostgreSQL to initialize (30 seconds)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        
        Write-Host "🧪 Testing database connection..." -ForegroundColor Blue
        $testResult = docker exec kebos-postgres psql -U ctp_user -d ctp_database -c "SELECT 'PostgreSQL Ready!' as status;" 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Database connection successful!" -ForegroundColor Green
            Write-Host $testResult
            
            Write-Host ""
            Write-Host "🎉 SETUP COMPLETE!" -ForegroundColor Green
            Write-Host "==================" -ForegroundColor Green
            Write-Host "✅ Docker Desktop: Running"
            Write-Host "✅ PostgreSQL: Ready on port 5432"
            Write-Host "✅ Database: ctp_database"
            Write-Host "✅ User: ctp_user"
            
            Write-Host ""
            Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
            Write-Host "1. Start your backend:" -ForegroundColor White
            Write-Host "   cd backend" -ForegroundColor Gray
            Write-Host "   uvicorn main:app --reload --port 3001" -ForegroundColor Gray
            Write-Host ""
            Write-Host "2. You should no longer see 'Database models not available'!" -ForegroundColor White
            Write-Host ""
            Write-Host "3. Test at: http://localhost:3001/docs" -ForegroundColor White
            
        } else {
            Write-Host "⚠️  Database still initializing. Try again in 1 minute:" -ForegroundColor Yellow
            Write-Host "docker exec kebos-postgres psql -U ctp_user -d ctp_database -c \"SELECT 'Ready!' as status;\"" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "📊 Container Status:" -ForegroundColor Blue
        docker ps --filter "name=kebos-postgres"
        
    } else {
        Write-Host "❌ Failed to start PostgreSQL container" -ForegroundColor Red
        Write-Host "Check logs with: docker logs kebos-postgres" -ForegroundColor Cyan
    }
    
} else {
    Write-Host ""
    Write-Host "⏰ Docker Desktop is taking longer than expected to start." -ForegroundColor Yellow
    Write-Host "This is normal on first installation." -ForegroundColor White
    Write-Host ""
    Write-Host "Please wait a few more minutes and try:" -ForegroundColor Cyan
    Write-Host "docker --version" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Once that works, run:" -ForegroundColor Cyan
    Write-Host "docker run -d --name kebos-postgres --restart unless-stopped -p 5432:5432 -e POSTGRES_DB=ctp_database -e POSTGRES_USER=ctp_user -e POSTGRES_PASSWORD=secure_ctp_password_2024 postgres:13" -ForegroundColor Gray
}
}
