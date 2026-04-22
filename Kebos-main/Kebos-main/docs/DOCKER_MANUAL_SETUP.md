# 🐳 Docker Setup - Manual Commands

## ✅ **Current Status**
- ✅ **Docker Desktop installed successfully**
- ⏳ **Docker Desktop starting up** (can take 2-5 minutes on first launch)
- 🎯 **Ready for PostgreSQL setup**

## 📋 **Wait for Docker Desktop to Start**

**You'll know Docker is ready when:**
1. Docker Desktop icon appears in system tray (bottom-right)
2. The icon stops animating and shows a whale
3. Running `docker --version` in PowerShell works

## 🚀 **Once Docker is Ready, Run These Commands:**

### **Step 1: Verify Docker is Working**
```powershell
docker --version
docker info
```

### **Step 2: Start PostgreSQL Database**
```powershell
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

### **Step 3: Wait and Test (30 seconds later)**
```powershell
# Check container is running
docker ps

# Test database connection  
docker exec kebos-postgres psql -U ctp_user -d ctp_database -c "SELECT 'Database ready!' as status;"
```

### **Step 4: Start Your Backend**
```powershell
cd "C:\Users\madhu\OneDrive\Desktop\PG\Kebos\backend"
uvicorn main:app --reload --port 3001
```

## 🎯 **Expected Results**

**After PostgreSQL is running, you should see:**
- ✅ No more "Database models not available" message
- ✅ All API endpoints fully functional
- ✅ Database-dependent features working (auth, audit logs, etc.)

## 📱 **Quick Status Check**

**Run this to check if Docker is ready:**
```powershell
docker --version
```

**If you get an error:** Docker is still starting - wait another minute

**If you see version info:** Docker is ready! Run the PostgreSQL setup commands above

## 🛠️ **Alternative: Use Docker Compose**

**If you prefer, use the existing Docker Compose setup:**
```powershell
cd "C:\Users\madhu\OneDrive\Desktop\PG\Kebos"

# Start PostgreSQL only
docker-compose -f docker-compose.ctp.yml up -d postgres

# Or start full stack
docker-compose -f docker-compose.ctp.yml up -d
```

## 🎉 **Final Test**

**Once everything is running, test your setup:**
```powershell
# Test health endpoint
curl http://localhost:3001/health

# Test database-dependent endpoint
curl http://localhost:3001/auth/auth/health
```

**You should see healthy responses without any database warnings!** 🚀

---

**💡 Tip:** Docker Desktop may require a restart of your computer on first installation. If you continue having issues, try restarting your PC and running the setup again.
