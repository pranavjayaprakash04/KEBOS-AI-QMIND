#!/bin/bash

# Production Deployment Script for CTP
# Run this script to deploy the Cyber Threat Platform

set -e

echo "🚀 Starting CTP Production Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required files exist
check_requirements() {
    print_status "Checking deployment requirements..."
    
    required_files=(
        ".env"
        "docker-compose.ctp.yml"
        "backend/Dockerfile"
        "frontend/Dockerfile"
        "frontend/nginx.conf"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file missing: $file"
            exit 1
        fi
    done
    
    print_status "All required files found ✓"
}

# Pre-deployment checks
pre_deployment_checks() {
    print_status "Running pre-deployment checks..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if .env is properly configured
    if grep -q "CHANGE_THIS" .env; then
        print_error "Please update the security configuration in .env file"
        print_warning "Search for 'CHANGE_THIS' and replace with secure values"
        exit 1
    fi
    
    print_status "Pre-deployment checks passed ✓"
}

# Build and deploy
deploy() {
    print_status "Building and deploying CTP services..."
    
    # Stop any existing services
    print_status "Stopping existing services..."
    docker-compose -f docker-compose.ctp.yml down --remove-orphans
    
    # Build services
    print_status "Building services..."
    docker-compose -f docker-compose.ctp.yml build --no-cache
    
    # Start services
    print_status "Starting services..."
    docker-compose -f docker-compose.ctp.yml up -d
    
    # Wait for services to be healthy
    print_status "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    print_status "Checking service health..."
    docker-compose -f docker-compose.ctp.yml ps
}

# Post-deployment verification
post_deployment_checks() {
    print_status "Running post-deployment verification..."
    
    # Check if services are running
    services=("timescaledb" "redis" "kafka" "backend" "frontend" "ollama")
    
    for service in "${services[@]}"; do
        if docker-compose -f docker-compose.ctp.yml ps "$service" | grep -q "Up"; then
            print_status "$service is running ✓"
        else
            print_error "$service is not running properly"
            docker-compose -f docker-compose.ctp.yml logs "$service"
        fi
    done
    
    # Test backend health endpoint
    print_status "Testing backend health endpoint..."
    if curl -f http://localhost:8000/health &> /dev/null; then
        print_status "Backend health check passed ✓"
    else
        print_warning "Backend health check failed - service may still be starting"
    fi
    
    # Test frontend
    print_status "Testing frontend..."
    if curl -f http://localhost:3000/health &> /dev/null; then
        print_status "Frontend health check passed ✓"
    else
        print_warning "Frontend health check failed - service may still be starting"
    fi
}

# Display final information
display_info() {
    echo ""
    echo "🎉 CTP Deployment Complete!"
    echo ""
    echo "📊 Access your services:"
    echo "  Frontend Dashboard: http://localhost:3000"
    echo "  Backend API:        http://localhost:8000"
    echo "  API Documentation:  http://localhost:8000/docs"
    echo "  Kafka UI:          http://localhost:9000"
    echo ""
    echo "📝 Important notes:"
    echo "  - Update DNS records to point to your server"
    echo "  - Configure SSL/TLS certificates for production"
    echo "  - Set up monitoring and alerting"
    echo "  - Schedule database backups"
    echo "  - Upload your trained autoencoder model to backend/models/"
    echo ""
    echo "🔧 Useful commands:"
    echo "  View logs:     docker-compose -f docker-compose.ctp.yml logs -f"
    echo "  Stop services: docker-compose -f docker-compose.ctp.yml down"
    echo "  Restart:       docker-compose -f docker-compose.ctp.yml restart"
    echo ""
}

# Main execution
main() {
    echo "🔐 CTP (Cyber Threat Platform) Production Deployment"
    echo "=================================================="
    
    check_requirements
    pre_deployment_checks
    deploy
    post_deployment_checks
    display_info
}

# Run main function
main "$@"
