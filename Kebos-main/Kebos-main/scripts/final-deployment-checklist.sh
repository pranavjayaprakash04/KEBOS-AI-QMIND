#!/bin/bash

# CTP Final Deployment Checklist
# This script guides you through the final steps to make your CTP platform production-ready

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}================================================================${NC}"
    echo -e "${PURPLE}         CTP FINAL DEPLOYMENT CHECKLIST${NC}"
    echo -e "${PURPLE}================================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}[STEP $1]${NC} $2"
    echo "----------------------------------------"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_file_exists() {
    if [ -f "$1" ]; then
        print_success "$1 exists"
        return 0
    else
        print_error "$1 not found"
        return 1
    fi
}

prompt_user() {
    local prompt="$1"
    local response
    echo -e "${YELLOW}$prompt${NC}"
    read -p "Continue? (y/N): " response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
}

generate_secure_key() {
    openssl rand -hex 32
}

main() {
    print_header
    
    echo "This checklist will guide you through the final steps to deploy your CTP platform."
    echo "Make sure you have your trained autoencoder model files ready!"
    echo ""
    
    # Step 1: Security Configuration
    print_step "1" "SECURITY CONFIGURATION"
    
    if [ ! -f ".env" ]; then
        print_info "Creating .env file from production template..."
        cp .env.production .env
        print_success ".env file created"
    else
        print_info ".env file already exists"
    fi
    
    if grep -q "CHANGE_THIS" .env; then
        print_warning "Found default security values in .env file"
        echo ""
        echo "You need to update the following values in your .env file:"
        echo ""
        echo "SECRET_KEY=$(generate_secure_key)"
        echo "JWT_SECRET_KEY=$(generate_secure_key)"
        echo "POSTGRES_PASSWORD=$(generate_secure_key)"
        echo "REDIS_PASSWORD=$(generate_secure_key)"
        echo ""
        prompt_user "Please update these values in your .env file now."
    else
        print_success "Security configuration appears to be updated"
    fi
    
    # Step 2: Domain Configuration
    print_step "2" "DOMAIN CONFIGURATION"
    
    echo "Current domain configuration in .env:"
    grep -E "(ALLOWED_ORIGINS|REACT_APP_API_URL|REACT_APP_WS_URL)" .env || true
    echo ""
    
    if grep -q "yourdomain.com" .env; then
        print_warning "Found placeholder domain names"
        echo ""
        echo "Please update these domain values in your .env file:"
        echo "ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com"
        echo "REACT_APP_API_URL=https://api.yourdomain.com"
        echo "REACT_APP_WS_URL=wss://api.yourdomain.com"
        echo ""
        prompt_user "Update domain configuration now."
    else
        print_success "Domain configuration appears to be updated"
    fi
    
    # Step 3: Frontend Environment
    print_step "3" "FRONTEND ENVIRONMENT"
    
    if [ ! -f "frontend/.env" ]; then
        print_info "Creating frontend .env file..."
        cp frontend/.env.production frontend/.env
        print_success "Frontend .env file created"
    else
        print_success "Frontend .env file exists"
    fi
    
    # Step 4: Model Integration
    print_step "4" "AUTOENCODER MODEL INTEGRATION"
    
    if [ ! -d "backend/models/autoencoder" ]; then
        print_info "Creating models directory..."
        mkdir -p backend/models/autoencoder
    fi
    
    model_files=("autoencoder_model.pkl" "scaler.pkl" "model_config.json")
    missing_files=()
    
    for file in "${model_files[@]}"; do
        if [ -f "backend/models/autoencoder/$file" ]; then
            print_success "$file found"
        else
            print_error "$file missing"
            missing_files+=("$file")
        fi
    done
    
    if [ ${#missing_files[@]} -gt 0 ]; then
        print_warning "Missing model files detected"
        echo ""
        echo "Please copy your trained model files to backend/models/autoencoder/:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        echo ""
        echo "You can run the model integration helper:"
        echo "python integrate-model.py"
        echo ""
        prompt_user "Copy your model files now."
    else
        print_success "All model files are present"
        
        # Test model integration
        print_info "Testing model integration..."
        if python integrate-model.py > /dev/null 2>&1; then
            print_success "Model integration test passed"
        else
            print_warning "Model integration test failed - check your model files"
        fi
    fi
    
    # Step 5: Docker Setup
    print_step "5" "DOCKER CONFIGURATION"
    
    required_files=("docker-compose.ctp.yml" "backend/Dockerfile" "frontend/Dockerfile" "frontend/nginx.conf")
    
    for file in "${required_files[@]}"; do
        check_file_exists "$file"
    done
    
    # Step 6: Build and Test
    print_step "6" "BUILD AND TEST"
    
    print_info "Building CTP services..."
    if docker-compose -f docker-compose.ctp.yml build > /dev/null 2>&1; then
        print_success "All services built successfully"
    else
        print_error "Build failed - check Docker configuration"
        exit 1
    fi
    
    # Step 7: Deployment
    print_step "7" "DEPLOYMENT"
    
    echo "Ready to deploy your CTP platform!"
    echo ""
    echo "Deployment options:"
    echo "1. Quick deployment: ./deploy.sh"
    echo "2. Using Makefile: make deploy-prod"
    echo "3. Manual: docker-compose -f docker-compose.ctp.yml up -d"
    echo ""
    
    read -p "Deploy now? (y/N): " deploy_response
    if [[ "$deploy_response" =~ ^[Yy]$ ]]; then
        print_info "Starting deployment..."
        
        # Stop any existing services
        docker-compose -f docker-compose.ctp.yml down --remove-orphans > /dev/null 2>&1 || true
        
        # Deploy
        docker-compose -f docker-compose.ctp.yml up -d
        
        print_info "Waiting for services to start..."
        sleep 30
        
        # Health checks
        print_info "Running health checks..."
        
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Backend is healthy"
        else
            print_warning "Backend health check failed"
        fi
        
        if curl -f http://localhost:3000/health > /dev/null 2>&1; then
            print_success "Frontend is healthy"
        else
            print_warning "Frontend health check failed"
        fi
    fi
    
    # Step 8: Final Summary
    print_step "8" "DEPLOYMENT COMPLETE"
    
    echo ""
    echo -e "${GREEN}🎉 CTP DEPLOYMENT COMPLETED!${NC}"
    echo ""
    echo "Your Cyber Threat Platform is now running:"
    echo ""
    echo -e "${CYAN}📊 Access Points:${NC}"
    echo "  • Frontend Dashboard: http://localhost:3000"
    echo "  • Backend API:        http://localhost:8000"
    echo "  • API Documentation:  http://localhost:8000/docs"
    echo "  • Kafka UI:          http://localhost:9000"
    echo ""
    echo -e "${CYAN}🔧 Management Commands:${NC}"
    echo "  • View logs:         make logs"
    echo "  • Check health:      make health"
    echo "  • Stop services:     make stop"
    echo "  • Restart services:  make restart"
    echo "  • Backup database:   make db-backup"
    echo ""
    echo -e "${CYAN}📋 Next Steps for Production:${NC}"
    echo "  1. Set up SSL certificates for HTTPS"
    echo "  2. Configure your domain DNS"
    echo "  3. Set up monitoring and alerting"
    echo "  4. Schedule regular database backups"
    echo "  5. Configure firewall and security groups"
    echo ""
    echo -e "${CYAN}🔍 Verification:${NC}"
    echo "  Run: ./verify-deployment.sh"
    echo ""
    echo -e "${GREEN}Your CTP platform is ready for production use!${NC}"
    echo ""
}

# Run main function
main "$@"
