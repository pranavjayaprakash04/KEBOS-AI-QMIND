Write-Host "CTP Frontend Setup Script" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host ""

# Check for Node.js
Write-Host "Checking for Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "Node.js not found! Please install Node.js from https://nodejs.org/" -ForegroundColor Red
    Write-Host "After installation, restart your terminal and run this script again." -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit 1
}

# Check for npm
Write-Host "Checking for npm..." -ForegroundColor Yellow
try {
    $npmVersion = npm --version
    Write-Host "npm found: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "npm not found! This should come with Node.js installation." -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit 1
}

Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
try {
    npm install
    Write-Host "Dependencies installed successfully!" -ForegroundColor Green
} catch {
    Write-Host "Failed to install dependencies!" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit 1
}

Write-Host ""
Write-Host "Creating .env file from template..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env file created from template" -ForegroundColor Green
} else {
    Write-Host ".env file already exists" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete! You can now run:" -ForegroundColor Green
Write-Host "  npm run dev    - Start development server" -ForegroundColor White
Write-Host "  npm run build  - Build for production" -ForegroundColor White
Write-Host ""
Read-Host "Press any key to exit"
