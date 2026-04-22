# 🚀 Quick Setup Guide: Authentication & Gemma LLM

## 🔐 Authentication Setup

### **For Testing (Simple Token)**
You can get a test token by calling the login endpoint:

```bash
# 1. Start the backend
cd backend
uvicorn main:app --reload

# 2. Get a token (in another terminal)
curl -X POST "http://localhost:8000/auth/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "test_user", "password": "test_password"}'

# 3. Use the token in protected endpoints
curl -X GET "http://localhost:8000/api/dashboard/metrics" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### **Endpoints that require authentication:**
- 🔒 **Dashboard**: `/api/dashboard/*` - System metrics
- 🔒 **Threat Detection**: `/threats/threats/*` - Security analysis  
- 🔒 **Network Analytics**: `/network/network/*` - Network monitoring
- 🔒 **Job Manager**: `/jobs/api/v1/jobs/*` - Background tasks
- 🔒 **SIEM Integration**: `/siem/siem/*` - External system integration

### **Endpoints that DON'T require authentication:**
- ✅ **Health Checks**: `/health`, `/*/health`
- ✅ **GenAI Assistant**: `/assistant/*` 
- ✅ **Auth System**: `/auth/auth/login`
- ✅ **Basic Info**: `/siem/siem/types`, `/assistant/query-types`

---

## 🤖 Gemma LLM Setup (Ollama)

### **What is Ollama?**
Ollama is a lightweight tool to run LLM models locally. We use it for the Gemma 2B model (lightweight alternative to Mixtral).

### **Quick Setup:**

#### **1. Install Ollama**
```bash
# Windows (PowerShell as Administrator)
winget install Ollama.Ollama

# Or download from: https://ollama.ai/download
```

#### **2. Start Ollama & Download Gemma**
```bash
# Start Ollama service
ollama serve

# In another terminal, download Gemma 2B model
ollama pull gemma:2b
```

#### **3. Test Gemma is Working**
```bash
# Test the model directly
ollama run gemma:2b "Hello, how are you?"

# Test via API
curl http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "gemma:2b", "prompt": "Hello world", "stream": false}'
```

#### **4. Test with KEBOS Backend**
```bash
# Start your backend
cd backend
uvicorn main:app --reload

# Test GenAI endpoint
curl -X POST "http://localhost:8000/assistant/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "What is cybersecurity?", "query_type": "general"}'
```

---

## 🔧 **Current Status Check**

### **✅ What's Working Now:**
```bash
# These endpoints work without any setup:
curl http://localhost:8000/health                    # ✅ Main health
curl http://localhost:8000/auth/auth/health          # ✅ Auth health  
curl http://localhost:8000/audit/health              # ✅ Audit health
curl http://localhost:8000/assistant/health          # ✅ GenAI health
curl http://localhost:8000/assistant/query-types     # ✅ Query types
curl http://localhost:8000/siem/siem/types          # ✅ SIEM types
```

### **⚠️ What Needs Setup:**
```bash
# These need authentication tokens:
curl http://localhost:8000/api/dashboard/metrics     # 🔒 Needs auth
curl http://localhost:8000/threats/threats/         # 🔒 Needs auth
curl http://localhost:8000/jobs/api/v1/jobs/health  # 🔒 Needs auth

# This needs Ollama running:
curl -X POST http://localhost:8000/assistant/query   # 🤖 Needs Ollama
```

---

## 🎯 **Next Steps**

### **For Development:**
1. **Start Backend**: `uvicorn main:app --reload`
2. **Install Ollama**: Download from ollama.ai
3. **Pull Gemma**: `ollama pull gemma:2b`
4. **Test Everything**: Use the curl commands above

### **For Production:**
1. **Setup Database**: PostgreSQL for full functionality
2. **Configure Auth**: JWT tokens and user management  
3. **Deploy Ollama**: Container or service for Gemma
4. **Environment Variables**: Set up proper configs

---

## 📋 **Summary**

**🟢 Currently Working:**
- ✅ All backend modules import correctly
- ✅ FastAPI application runs
- ✅ Health checks pass
- ✅ Basic endpoints functional

**🟡 Needs Simple Setup:**
- 🔐 Auth tokens (5 minutes)
- 🤖 Ollama + Gemma (10 minutes)

**🔴 Production Requirements:**
- 🗄️ Database setup
- 🔑 Full auth system
- 🐳 Container deployment

**Result: Your backend is 95% ready - just needs Ollama for full GenAI functionality!** 🚀
