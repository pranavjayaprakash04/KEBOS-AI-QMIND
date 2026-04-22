Write-Host "🐳 KEBOS Docker Setup" -ForegroundColor Blue
Write-Host "===================" -ForegroundColor Blue

# Check Docker status
Write-Host "Checking Docker..." -ForegroundColor Yellow
try {
    docker --version
    Write-Host "✅ Docker is ready!" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not ready. Please wait for Docker Desktop to start." -ForegroundColor Red
    exit 1
}

# Remove existing container if present
Write-Host "Cleaning up existing containers..." -ForegroundColor Yellow
docker stop kebos-postgres 2>$null
docker rm kebos-postgres 2>$null

# Start PostgreSQL
Write-Host "Starting PostgreSQL container..." -ForegroundColor Green
docker run -d --name kebos-postgres --restart unless-stopped -p 5432:5432 -e POSTGRES_DB=ctp_database -e POSTGRES_USER=ctp_user -e POSTGRES_PASSWORD=secure_ctp_password_2024 -v kebos_postgres_data:/var/lib/postgresql/data postgres:13

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PostgreSQL started successfully!" -ForegroundColor Green
    
    Write-Host "Waiting for database to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    
    Write-Host "Testing connection..." -ForegroundColor Blue
    docker exec kebos-postgres psql -U ctp_user -d ctp_database -c "SELECT 'Ready!' as status;"
    
    Write-Host ""
    Write-Host "🎉 Setup Complete!" -ForegroundColor Green
    Write-Host "Database is running on localhost:5432" -ForegroundColor White
    Write-Host ""
    Write-Host "Next: Start your backend with:" -ForegroundColor Cyan
    Write-Host "cd backend" -ForegroundColor Gray
    Write-Host "uvicorn main:app --reload --port 3001" -ForegroundColor Gray
    
} else {
    Write-Host "❌ Failed to start PostgreSQL" -ForegroundColor Red
}
