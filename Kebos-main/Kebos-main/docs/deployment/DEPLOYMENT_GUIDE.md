# CTP Production Deployment Guide

## 🚀 **DEPLOYMENT READINESS CHECKLIST**

### **1. CRITICAL SECURITY CONFIGURATION** ⚠️

#### **A. Environment Variables**
1. Copy `.env.production` to `.env`
2. **MUST CHANGE** all security-related variables:
   ```bash
   SECRET_KEY=your-256-bit-secret-key
   JWT_SECRET_KEY=your-different-256-bit-secret-key
   POSTGRES_PASSWORD=your-strong-database-password
   REDIS_PASSWORD=your-strong-redis-password
   ```

#### **B. Domain Configuration**
Update these in `.env`:
```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_WS_URL=wss://api.yourdomain.com
```

### **2. INFRASTRUCTURE REQUIREMENTS**

#### **A. Server Specifications**
- **Minimum:** 8GB RAM, 4 CPU cores, 100GB SSD
- **Recommended:** 16GB RAM, 8 CPU cores, 200GB SSD
- **OS:** Ubuntu 20.04+ or similar Linux distribution

#### **B. Required Software**
- Docker Engine 20.10+
- Docker Compose 2.0+
- SSL certificates (Let's Encrypt recommended)

### **3. DEPLOYMENT STEPS**

#### **Step 1: Clone and Setup**
```bash
git clone https://github.com/Madhumith-R/kebos-frontend.git
cd kebos-frontend
cp .env.production .env
# Edit .env with your secure values
```

#### **Step 2: Security Configuration**
```bash
# Generate secure secret keys
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 32  # For JWT_SECRET_KEY

# Update .env file with generated keys
nano .env
```

#### **Step 3: Deploy**
```bash
chmod +x deploy.sh
./deploy.sh
```

#### **Step 4: SSL/TLS Setup** (Production)
```bash
# Using Certbot for Let's Encrypt
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Update nginx configuration with SSL
# Restart frontend service
docker-compose -f docker-compose.ctp.yml restart frontend
```

### **4. MODEL INTEGRATION**

#### **A. Autoencoder Model Upload**
```bash
# Create models directory if it doesn't exist
mkdir -p backend/models/autoencoder

# Copy your trained model files
cp your_autoencoder_model.pkl backend/models/autoencoder/
cp your_scaler.pkl backend/models/autoencoder/
cp model_config.json backend/models/autoencoder/

# Restart backend to load model
docker-compose -f docker-compose.ctp.yml restart backend
```

#### **B. Model API Integration**
Update your threat detection service to load the model:
```python
# In backend/threat_detection/models.py
import pickle
import os

def load_autoencoder_model():
    model_path = os.getenv('AUTOENCODER_MODEL_PATH', '/app/models/autoencoder')
    model_file = os.path.join(model_path, 'autoencoder_model.pkl')
    scaler_file = os.path.join(model_path, 'scaler.pkl')
    
    if os.path.exists(model_file) and os.path.exists(scaler_file):
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        with open(scaler_file, 'rb') as f:
            scaler = pickle.load(f)
        return model, scaler
    else:
        raise FileNotFoundError("Autoencoder model files not found")
```

### **5. POST-DEPLOYMENT TASKS**

#### **A. Monitoring Setup**
- Set up log aggregation (ELK Stack or similar)
- Configure application performance monitoring
- Set up alerting for critical services

#### **B. Backup Strategy**
```bash
# Database backup
docker exec ctp_timescaledb pg_dump -U ctp_user ctp_database > backup_$(date +%Y%m%d).sql

# Volume backup
docker run --rm -v ctp_timescaledb_data:/data -v $(pwd):/backup alpine tar czf /backup/db_backup_$(date +%Y%m%d).tar.gz /data
```

#### **C. Security Hardening**
- Enable firewall (UFW or iptables)
- Set up fail2ban for SSH protection
- Regular security updates
- Network segmentation if possible

### **6. VERIFICATION CHECKLIST**

#### **Health Checks**
- [ ] Frontend accessible at your domain
- [ ] Backend API responding at /health
- [ ] Database connections working
- [ ] Kafka services running
- [ ] WebSocket connections working
- [ ] SSL certificates valid
- [ ] Model loading successfully

#### **Security Checks**
- [ ] All default passwords changed
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] Security headers present
- [ ] No sensitive data in logs

### **7. MAINTENANCE**

#### **Regular Tasks**
- Monitor disk space usage
- Review application logs
- Update dependencies monthly
- Backup databases weekly
- Certificate renewal (if using Let's Encrypt)

#### **Scaling Considerations**
- Use Docker Swarm or Kubernetes for multi-node deployment
- Implement load balancing for high availability
- Consider database clustering for large deployments

### **8. TROUBLESHOOTING**

#### **Common Issues**
```bash
# View service logs
docker-compose -f docker-compose.ctp.yml logs [service_name]

# Restart specific service
docker-compose -f docker-compose.ctp.yml restart [service_name]

# Check service health
docker-compose -f docker-compose.ctp.yml ps

# Database connection issues
docker exec -it ctp_timescaledb psql -U ctp_user -d ctp_database
```

### **9. SUPPORT CONTACTS**

For deployment issues:
- Check logs first: `docker-compose -f docker-compose.ctp.yml logs`
- Review configuration files
- Verify network connectivity
- Check resource usage: `docker stats`

---

## **⚠️ CRITICAL REMINDER**

**BEFORE GOING LIVE:**
1. ✅ Change ALL default passwords and secret keys
2. ✅ Configure proper domain names and SSL
3. ✅ Upload your trained autoencoder model
4. ✅ Test all functionalities in staging environment
5. ✅ Set up monitoring and alerting
6. ✅ Configure backups
7. ✅ Review security settings

**Your platform will be ready for production deployment once these steps are completed!**
