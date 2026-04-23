@echo off
echo CTP Frontend Setup Script
echo ==========================

echo.
echo Checking for Node.js installation...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Node.js not found! Please install Node.js from https://nodejs.org/
    echo After installation, restart your terminal and run this script again.
    pause
    exit /b 1
)

echo Node.js found!
echo.

echo Checking for npm...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo npm not found! This should come with Node.js installation.
    pause
    exit /b 1
)

echo npm found!
echo.

echo Installing dependencies...
npm install

if %errorlevel% neq 0 (
    echo Failed to install dependencies!
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
echo.

echo Creating .env file from template...
if not exist .env (
    copy .env.example .env
    echo .env file created from template
) else (
    echo .env file already exists
)

echo.
echo Setup complete! You can now run:
echo   npm run dev    - Start development server
echo   npm run build  - Build for production
echo.
pause
