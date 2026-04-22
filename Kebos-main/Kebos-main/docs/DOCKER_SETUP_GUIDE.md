# 🐳 Docker Setup Guide for KEBOS Backend

## 📋 **Step 1: Install Docker Desktop**

### **Windows Installation:**

#### **Option A: Using Winget (Recommended)**
```powershell
# Open PowerShell as Administrator and run:
winget install Docker.DockerDesktop
```

#### **Option B: Manual Download**
1. Go to: https://www.docker.com/products/docker-desktop/
2. Download "Docker Desktop for Windows"
3. Run the installer
4. Restart your computer when prompted

#### **Option C: Using Chocolatey**
```powershell
# If you have Chocolatey installed:
choco install docker-desktop
```

### **After Installation:**
1. **Start Docker Desktop** from the Start menu
2. **Wait for Docker to start** (you'll see the Docker icon in system tray)
3. **Verify installation** by running: `docker --version`

---

## 📋 **Step 2: Set Up PostgreSQL Database**

Once Docker is installed and running, execute these commands:

### **Start PostgreSQL Container:**
```bash
# Navigate to your project directory
cd "C:\Users\madhu\OneDrive\Desktop\PG\Kebos"

# Start PostgreSQL with your exact configuration
docker run -d \
  --name kebos-postgres \
  --restart unless-stopped \
  -p 5432:5432 \
  -e POSTGRES_DB=ctp_database \
  -e POSTGRES_USER=ctp_user \
  -e POSTGRES_PASSWORD=secure_ctp_password_2024 \
  -v kebos_postgres_data:/var/lib/postgresql/data \
  postgres:13
```

### **Verify Database is Running:**
```bash
# Check container status
docker ps

# Check database logs
docker logs kebos-postgres

# Test database connection
docker exec -it kebos-postgres psql -U ctp_user -d ctp_database -c "SELECT version();"
```

---

## 📋 **Step 3: Initialize Database Schema**

After PostgreSQL is running, set up the database schema:

```bash
cd backend

# Install database dependencies if needed
pip install alembic psycopg2-binary

# Run database migrations
alembic upgrade head

# Or run the initialization script
python init_db.py
```

---

## 📋 **Step 4: Test Your Setup**

### **Test Database Connection:**
```bash
cd backend
python -c "
from common.db import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version();'))
        print('✅ Database connected successfully!')
        print(f'PostgreSQL: {result.fetchone()[0][:50]}...')
except Exception as e:
    print(f'❌ Connection failed: {e}')
"
```

### **Test Backend with Database:**
```bash
# Start your backend
uvicorn main:app --reload --port 3001

# In another terminal, test an endpoint that requires database
curl -X GET "http://localhost:3001/health"
```

---

## 📋 **Step 5: Docker Compose (Alternative)**

Your project already has Docker Compose configuration. You can use it instead:

```bash
# Start PostgreSQL only
docker-compose -f docker-compose.ctp.yml up -d postgres

# Or start the full stack
docker-compose -f docker-compose.ctp.yml up -d

# Stop services
docker-compose -f docker-compose.ctp.yml down
```

---

## 🛠️ **Useful Docker Commands**

### **Managing PostgreSQL Container:**
```bash
# Start the container
docker start kebos-postgres

# Stop the container
docker stop kebos-postgres

# Remove the container (data will be preserved in volume)
docker rm kebos-postgres

# View logs
docker logs kebos-postgres -f

# Connect to database
docker exec -it kebos-postgres psql -U ctp_user -d ctp_database
```

### **Database Management:**
```bash
# Backup database
docker exec kebos-postgres pg_dump -U ctp_user ctp_database > backup.sql

# Restore database
docker exec -i kebos-postgres psql -U ctp_user -d ctp_database < backup.sql

# Reset database (removes all data)
docker exec kebos-postgres psql -U ctp_user -d ctp_database -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

---

## 🎯 **Expected Results After Setup**

Once Docker and PostgreSQL are running, you should see:

### **✅ Successful Setup Indicators:**
- `docker ps` shows `kebos-postgres` container running
- Backend logs show database connection successful
- No more "Database models not available" messages
- All API endpoints working with full functionality

### **🧪 Test Full Functionality:**
```bash
# Test authentication (now works with database)
curl -X POST "http://localhost:3001/auth/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Test audit logging (now works with database)  
curl -X GET "http://localhost:3001/audit/health"

# Test user management (now works with database)
curl -X GET "http://localhost:3001/auth/auth/users"
```

---

## ⚠️ **Troubleshooting**

### **If Docker installation fails:**
- Ensure Windows 10/11 with WSL2 enabled
- Enable Hyper-V in Windows Features
- Restart computer after installation

### **If PostgreSQL won't start:**
```bash
# Check if port 5432 is already in use
netstat -an | findstr :5432

# Use different port if needed
docker run -d --name kebos-postgres -p 5433:5432 ...
# Then update .env file: POSTGRES_PORT=5433
```

### **If database connection fails:**
- Verify container is running: `docker ps`
- Check container logs: `docker logs kebos-postgres`
- Verify environment variables match your `.env` file

---

## 🚀 **Quick Start Commands**

**After Docker Desktop is installed and running:**
```bash
# 1. Start PostgreSQL
docker run -d --name kebos-postgres --restart unless-stopped -p 5432:5432 -e POSTGRES_DB=ctp_database -e POSTGRES_USER=ctp_user -e POSTGRES_PASSWORD=secure_ctp_password_2024 postgres:13

# 2. Wait 30 seconds for PostgreSQL to start

# 3. Test connection
docker exec kebos-postgres psql -U ctp_user -d ctp_database -c "SELECT 'Database ready!'"

# 4. Start your backend
cd backend
uvicorn main:app --reload --port 3001
```

**Expected result:** No more "Database models not available" message! 🎉
