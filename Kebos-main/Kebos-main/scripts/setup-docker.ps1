# Docker Setup Script for KEBOS
# Run this after Docker Desktop finishes starting

Write-Host "🐳 KEBOS Docker Setup Script" -ForegroundColor Blue
Write-Host "================================" -ForegroundColor Blue
Write-Host ""

# Check if Docker is available
Write-Host "⏳ Checking Docker status..." -ForegroundColor Yellow
$dockerReady = $false
$attempts = 0
$maxAttempts = 30

while (-not $dockerReady -and $attempts -lt $maxAttempts) {
    try {
        $null = docker version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $dockerReady = $true
            Write-Host "✅ Docker is ready!" -ForegroundColor Green
        }
    }
    catch {
        # Docker not ready yet
    }
    
    if (-not $dockerReady) {
        $attempts++
        Write-Host "⏳ Waiting for Docker to start... ($attempts/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

if (-not $dockerReady) {
    Write-Host "❌ Docker failed to start within 2.5 minutes" -ForegroundColor Red
    Write-Host "💡 Please check Docker Desktop manually and run this script again" -ForegroundColor Cyan
    exit 1
}

# Show Docker version
Write-Host ""
Write-Host "📋 Docker Information:" -ForegroundColor Blue
docker version --format "Version: {{.Client.Version}}"
docker info --format "Status: {{.ServerVersion}}"

Write-Host ""
Write-Host "🗄️ Setting up PostgreSQL database..." -ForegroundColor Blue

# Remove existing container if it exists
$existingContainer = docker ps -a --filter "name=kebos-postgres" --format "{{.Names}}"
if ($existingContainer -eq "kebos-postgres") {
    Write-Host "⚠️  Removing existing kebos-postgres container..." -ForegroundColor Yellow
    docker stop kebos-postgres 2>$null
    docker rm kebos-postgres 2>$null
}

# Start PostgreSQL container
Write-Host "🚀 Starting PostgreSQL container..." -ForegroundColor Green
$postgresCommand = @"
docker run -d \
  --name kebos-postgres \
  --restart unless-stopped \
  -p 5432:5432 \
  -e POSTGRES_DB=ctp_database \
  -e POSTGRES_USER=ctp_user \
  -e POSTGRES_PASSWORD=secure_ctp_password_2024 \
  -v kebos_postgres_data:/var/lib/postgresql/data \
  postgres:13
"@

# Execute the command
Invoke-Expression $postgresCommand

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL container started successfully!" -ForegroundColor Green
    
    # Wait for PostgreSQL to be ready
    Write-Host ""
    Write-Host "⏳ Waiting for PostgreSQL to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    
    # Test database connection
    Write-Host "🧪 Testing database connection..." -ForegroundColor Blue
    $testResult = docker exec kebos-postgres psql -U ctp_user -d ctp_database -c "SELECT 'Database ready!' as status;" 2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Database connection successful!" -ForegroundColor Green
        Write-Host $testResult
    } else {
        Write-Host "⚠️  Database still initializing... give it another 30 seconds" -ForegroundColor Yellow
    }
    
    # Show container status
    Write-Host ""
    Write-Host "📊 Container Status:" -ForegroundColor Blue
    docker ps --filter "name=kebos-postgres" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    Write-Host ""
    Write-Host "🎉 Setup Complete!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Blue
    Write-Host "✅ Docker Desktop: Running" -ForegroundColor Green
    Write-Host "✅ PostgreSQL: Started on port 5432" -ForegroundColor Green
    Write-Host "✅ Database: ctp_database" -ForegroundColor Green
    Write-Host "✅ User: ctp_user" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Start your backend:" -ForegroundColor White
    Write-Host "   cd backend" -ForegroundColor Gray
    Write-Host "   uvicorn main:app --reload --port 3001" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. You should no longer see 'Database models not available'" -ForegroundColor White
    Write-Host ""
    Write-Host "3. Test full functionality at: http://localhost:3001/docs" -ForegroundColor White
    
} else {
    Write-Host "❌ Failed to start PostgreSQL container" -ForegroundColor Red
    Write-Host "Check Docker logs with: docker logs kebos-postgres" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🛠️  Useful Commands:" -ForegroundColor Blue
Write-Host "View container logs: docker logs kebos-postgres" -ForegroundColor Gray
Write-Host "Stop database: docker stop kebos-postgres" -ForegroundColor Gray  
Write-Host "Start database: docker start kebos-postgres" -ForegroundColor Gray
Write-Host "Connect to database: docker exec -it kebos-postgres psql -U ctp_user -d ctp_database" -ForegroundColor Gray
