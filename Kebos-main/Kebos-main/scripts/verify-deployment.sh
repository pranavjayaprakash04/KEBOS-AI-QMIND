#!/bin/bash

# CTP Deployment Verification Script
# This script verifies that your CTP deployment is ready for production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0

print_header() {
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}  CTP Deployment Verification${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""
}

print_status() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_CHECKS++))
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_CHECKS++))
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

run_check() {
    local description="$1"
    local command="$2"
    
    ((TOTAL_CHECKS++))
    echo -n "Checking $description... "
    
    if eval "$command" &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
        print_status "$description"
    else
        echo -e "${RED}✗${NC}"
        print_error "$description"
    fi
}

# Function to check if a service is running
check_service() {
    local service_name="$1"
    local description="$2"
    
    ((TOTAL_CHECKS++))
    if docker-compose -f docker-compose.ctp.yml ps "$service_name" | grep -q "Up"; then
        print_status "$description is running"
    else
        print_error "$description is not running"
        docker-compose -f docker-compose.ctp.yml logs "$service_name" | tail -5
    fi
}

# Function to check HTTP endpoint
check_endpoint() {
    local url="$1"
    local description="$2"
    
    ((TOTAL_CHECKS++))
    if curl -f -s "$url" > /dev/null; then
        print_status "$description endpoint is responding"
    else
        print_error "$description endpoint is not responding"
    fi
}

main() {
    print_header
    
    echo "Starting CTP deployment verification..."
    echo ""
    
    # Check if required files exist
    echo "📁 Checking required files..."
    run_check "docker-compose.ctp.yml exists" "[ -f docker-compose.ctp.yml ]"
    run_check ".env file exists" "[ -f .env ]"
    run_check "backend/Dockerfile exists" "[ -f backend/Dockerfile ]"
    run_check "frontend/Dockerfile exists" "[ -f frontend/Dockerfile ]"
    run_check "frontend/nginx.conf exists" "[ -f frontend/nginx.conf ]"
    echo ""
    
    # Check security configuration
    echo "🔒 Checking security configuration..."
    if [ -f .env ]; then
        if grep -q "CHANGE_THIS" .env; then
            print_error "Default security values found in .env - please update them"
        else
            print_status "Security configuration appears to be updated"
        fi
        
        if grep -q "SECRET_KEY.*=" .env && [ "$(grep 'SECRET_KEY' .env | cut -d'=' -f2 | wc -c)" -gt 20 ]; then
            print_status "SECRET_KEY is configured"
        else
            print_error "SECRET_KEY is not properly configured"
        fi
    fi
    echo ""
    
    # Check Docker services
    echo "🐳 Checking Docker services..."
    run_check "Docker is running" "docker info"
    run_check "Docker Compose is available" "docker-compose --version"
    echo ""
    
    # Check running services
    echo "⚙️ Checking CTP services..."
    check_service "timescaledb" "TimescaleDB database"
    check_service "redis" "Redis cache"
    check_service "kafka" "Kafka message broker"
    check_service "backend" "Backend API"
    check_service "frontend" "Frontend application"
    check_service "ollama" "Ollama LLM service"
    echo ""
    
    # Check service endpoints
    echo "🌐 Checking service endpoints..."
    check_endpoint "http://localhost:8000/health" "Backend health"
    check_endpoint "http://localhost:3000/health" "Frontend health"
    check_endpoint "http://localhost:8000/docs" "API documentation"
    echo ""
    
    # Check database connectivity
    echo "🗄️ Checking database connectivity..."
    ((TOTAL_CHECKS++))
    if docker-compose -f docker-compose.ctp.yml exec -T timescaledb pg_isready -U ctp_user &> /dev/null; then
        print_status "Database is accepting connections"
    else
        print_error "Database is not accepting connections"
    fi
    echo ""
    
    # Check for model files
    echo "🤖 Checking AI model files..."
    if [ -d "backend/models/autoencoder" ]; then
        if [ -f "backend/models/autoencoder/autoencoder_model.pkl" ]; then
            print_status "Autoencoder model file found"
        else
            print_warning "Autoencoder model file not found - upload your trained model"
        fi
        
        if [ -f "backend/models/autoencoder/scaler.pkl" ]; then
            print_status "Scaler file found"
        else
            print_warning "Scaler file not found - upload your scaler"
        fi
    else
        print_warning "Models directory not found - create backend/models/autoencoder/ and upload your models"
    fi
    echo ""
    
    # Check volumes and persistence
    echo "💾 Checking data persistence..."
    run_check "TimescaleDB volume exists" "docker volume ls | grep -q timescaledb_data"
    run_check "Redis volume exists" "docker volume ls | grep -q redis_data"
    run_check "Kafka volume exists" "docker volume ls | grep -q kafka_data"
    echo ""
    
    # Security checks
    echo "🔐 Additional security checks..."
    ((TOTAL_CHECKS++))
    if docker-compose -f docker-compose.ctp.yml exec backend curl -f http://localhost:8000/health &> /dev/null; then
        print_status "Internal service communication working"
    else
        print_error "Internal service communication failed"
    fi
    echo ""
    
    # Summary
    echo "📊 Verification Summary:"
    echo "========================"
    echo "Total Checks: $TOTAL_CHECKS"
    echo -e "Passed: ${GREEN}$PASSED_CHECKS${NC}"
    echo -e "Failed: ${RED}$FAILED_CHECKS${NC}"
    echo ""
    
    if [ $FAILED_CHECKS -eq 0 ]; then
        echo -e "${GREEN}🎉 All checks passed! Your CTP deployment is ready for production.${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Configure your domain DNS to point to this server"
        echo "2. Set up SSL/TLS certificates"
        echo "3. Upload your trained autoencoder model if not already done"
        echo "4. Set up monitoring and alerting"
        echo "5. Configure automated backups"
        echo ""
        echo "Access your CTP platform:"
        echo "• Frontend: http://localhost:3000"
        echo "• Backend API: http://localhost:8000"
        echo "• API Docs: http://localhost:8000/docs"
        echo "• Kafka UI: http://localhost:9000"
    else
        echo -e "${RED}❌ Some checks failed. Please fix the issues before deploying to production.${NC}"
        echo ""
        echo "Common fixes:"
        echo "• Update security configuration in .env file"
        echo "• Ensure all services are running: make start"
        echo "• Check service logs: make logs"
        echo "• Verify Docker and Docker Compose installation"
        exit 1
    fi
}

# Run main function
main "$@"
