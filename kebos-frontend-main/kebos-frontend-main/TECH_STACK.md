# KEBOS - Cyber Threat Platform Tech Stack

## 🚀 Overview
This document outlines the complete technology stack used in the KEBOS Cyber Threat Platform system.

## 🖥️ Frontend Technologies

### **Core Framework**
- **React 18.2+** - Modern React with hooks and functional components
- **TypeScript 5.0+** - Type-safe JavaScript development
- **Vite 4.4+** - Fast build tool and development server

### **Forms & Validation**
- **React Hook Form** - Performant form management
- **Zod** - TypeScript-first schema validation
- **Hookform Resolvers** - Form validation integration

### **HTTP & Real-time Communication**
- **Axios** - HTTP client for API requests
- **Socket.io Client** - Real-time bidirectional communication
- **React Hot Toast** - Elegant toast notifications

### **Styling & UI**
- **Tailwind CSS 3.3+** - Utility-first CSS framework
- **Framer Motion** - Advanced animations and transitions
- **Lucide React** - Modern icon library
- **Chart.js & Recharts** - Data visualization libraries
- **Responsive Design** - Mobile-first approach

### **State & Routing**
- **React Context API** - Global state management
- **React Router DOM 6.15+** - Client-side routing
- **Zustand** - Lightweight state management
- **TanStack Query** - Server state management and caching

## ⚙️ Backend Technologies

### **Core Framework**
- **FastAPI** - Modern Python web framework for APIs
- **Python 3.11+** - Programming language
- **Uvicorn** - ASGI server for FastAPI

### **Database & ORM**
- **PostgreSQL** - Primary relational database
- **TimescaleDB** - Time-series database extension
- **InfluxDB** - Time-series database for metrics
- **SQLAlchemy 2.0+** - Python ORM for database operations
- **Alembic** - Database migration tool

### **Data Validation & Serialization**
- **Pydantic** - Data validation and serialization
- **OpenAPI/Swagger** - Automatic API documentation

### **Task Processing**
- **Celery** - Distributed task queue
- **Redis** - Message broker and caching

### **Machine Learning**
- **PyTorch** - Deep learning framework
- **TensorFlow** - Machine learning platform
- **Transformers** - Hugging Face transformer models
- **LangChain** - LLM integration framework
- **MLflow** - Model registry and tracking
- **Optuna** - Hyperparameter optimization
- **scikit-learn** - Traditional machine learning library
- **NumPy & Pandas** - Data manipulation and analysis

### **Adversarial ML & Security**
- **Adversarial Robustness Toolbox** - ML security testing
- **Foolbox** - Adversarial attack library
- **OpenCV** - Computer vision library
- **SciPy & Statsmodels** - Statistical analysis

### **GenAI Assistant**
- **Gemma LLM** - Lightweight language model for threat analysis
- **RAG (Retrieval-Augmented Generation)** - Context-aware AI responses
- **Sentence Transformers** - Semantic search and embeddings
- **Conversation Context** - Multi-turn conversation management
- **MITRE ATT&CK Integration** - Threat framework knowledge

### **Post-Quantum Cryptography**
- **pqcrypto** - Production-ready NIST PQC implementations
- **ML-KEM (Kyber)** - Post-quantum key encapsulation (512/768/1024)
- **ML-DSA (Dilithium)** - Post-quantum digital signatures (44/65/87)
- **Hybrid Encryption** - Classical + post-quantum cryptography
- **Lattice-based Cryptography** - Advanced quantum-resistant algorithms

### **Classical Cryptography**
- **cryptography** - Python cryptographic primitives
- **AEAD (AES-GCM)** - Authenticated encryption
- **HKDF** - Key derivation functions
- **JWT** - JSON Web Tokens for authentication

### **Message Streaming**
- **Apache Kafka** - Event streaming platform
- **Confluent Kafka** - Enhanced Kafka client
- **aiokafka** - Async Kafka client for Python
- **Kafka UI** - Web interface for Kafka management
- **WebSocket** - Real-time communication

### **Network Analysis & Security**
- **Scapy** - Packet manipulation and analysis
- **GeoIP2** - IP geolocation database
- **netaddr** - Network address manipulation
- **ipaddress** - IP address handling utilities

### **Security & Authentication**
- **NIST Post-Quantum Standards** - Future-proof encryption
- **Multi-level Security** - NIST Level 1, 3, and 5 support
- **Secure Key Management** - Automated key generation and rotation
- **Password Hashing** - Secure credential storage
- **CORS** - Cross-origin resource sharing

## 🐳 DevOps & Infrastructure

### **Containerization**
- **Docker** - Application containerization
- **Docker Compose** - Multi-container orchestration

### **Development Tools**
- **Git** - Version control
- **GitHub** - Code repository and collaboration
- **npm** - Package management (Frontend)
- **pip** - Package management (Backend)

### **Testing & Quality**
- **Jest** - JavaScript testing framework
- **React Testing Library** - Component testing utilities
- **Storybook** - Component development and documentation
- **ESLint** - JavaScript/TypeScript linting
- **TypeScript Compiler** - Type checking and compilation

## 📁 Project Structure

```
KEBOS Cyber Threat Platform/
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page-level components
│   │   ├── contexts/      # React Context providers
│   │   └── services/      # API client services
│   └── package.json
├── backend/               # FastAPI backend
│   ├── main.py           # FastAPI application entry
│   ├── audit_logger/     # Audit logging module
│   ├── auth/             # Authentication module
│   ├── common/           # Shared utilities and services
│   │   ├── celery_app.py # Celery configuration
│   │   ├── workflow_api.py # Workflow management API
│   │   └── utils.py      # Common utilities
│   ├── genai_assistant/  # AI assistant & RAG module
│   │   ├── services.py   # GenAI services and RAG implementation
│   │   ├── models.py     # Pydantic models for AI queries
│   │   └── api.py        # GenAI API endpoints
│   ├── job_manager/      # Background job management
│   │   ├── services.py   # Job scheduling and tracking
│   │   ├── api.py        # Job management API
│   │   └── tasks.py      # Celery task definitions
│   ├── messaging/        # Secure messaging & crypto modules
│   │   ├── crypto_pq_production.py  # Production PQC implementation
│   │   ├── lattice_pqc.py          # Lattice-based cryptography
│   │   ├── secure_messaging.py     # Encrypted messaging
│   │   └── websocket.py            # Real-time communication
│   ├── threat_detection/ # Threat detection module
│   ├── network_analytics/ # Network analysis module
│   ├── siem_integration/ # SIEM integration module
│   ├── security.py       # Core security utilities
│   └── requirements.txt
└── docker-compose.yml    # Container orchestration
```

## 🔧 Key Features

### **Frontend Capabilities**
- Real-time dashboard with live data visualization
- Attack simulation interface
- Threat detection monitoring
- AI assistant chat interface
- Interactive charts and analytics
- Form validation and user input handling
- Real-time notifications and alerts
- User management
- Audit trail visualization
- Secure messaging interface

### **Backend Capabilities**
- RESTful API endpoints
- Real-time threat detection
- Attack simulation engine
- AI-powered threat analysis assistant
- RAG-based contextual responses
- Background job management and scheduling
- Workflow orchestration and monitoring
- Time-series data processing
- Audit logging system
- User authentication & authorization
- Background task processing
- Post-quantum secure messaging
- Network analytics and monitoring
- SIEM integration
- Packet analysis and network forensics

### **Cryptographic Features**
- **NIST Level 1-5 Security** - Multiple security levels (128/192/256-bit)
- **Future-Proof Encryption** - Quantum-resistant algorithms
- **Hybrid Crypto Systems** - Classical + post-quantum combination
- **Key Management** - Automated key generation and rotation
- **Digital Signatures** - Post-quantum authentication
- **Secure Messaging** - End-to-end encrypted communications
- **Performance Optimization** - Configurable security vs. speed

### **Advanced Security**
- **Lattice-based Cryptography** - Cutting-edge quantum resistance
- **Multi-algorithm Support** - Kyber/Dilithium family algorithms
- **Compression Integration** - Optimized encrypted data transfer
- **Error Handling** - Robust cryptographic error management
- **Logging & Monitoring** - Comprehensive security event tracking

### **AI-Powered Analysis**
- **Context-Aware Responses** - RAG-enhanced threat intelligence
- **Multi-Query Types** - Threat analysis, incident response, MITRE lookups
- **Conversation Management** - Persistent session context
- **Semantic Search** - Vector-based knowledge retrieval
- **Real-time Integration** - Live data from SIEM, network, and threat feeds
- **Adversarial ML Detection** - Model security and robustness testing
- **Deep Learning Models** - Advanced pattern recognition for threats

### **Workflow & Job Management**
- **Distributed Task Processing** - Celery-based background jobs
- **Workflow Orchestration** - Multi-step process automation
- **Job Scheduling** - Automated task execution
- **Progress Tracking** - Real-time job status monitoring
- **Error Handling** - Robust failure recovery mechanisms

## 🚀 Development & Deployment

### **Local Development**
```bash
# Frontend
npm run dev

# Backend
uvicorn main:app --reload

# Full Stack
docker-compose up -d
```

### **Production Deployment**
- **Docker containers** for consistent deployment
- **Environment-based configuration**
- **Health checks and monitoring**
- **Post-quantum crypto ready** for future threats
- **Scalable security architecture**

## 🔒 Security Configurations

### **PQC Security Levels**
- **Recommended**: ML-KEM-768 + ML-DSA-65 (NIST Level 3)
- **High Security**: ML-KEM-1024 + ML-DSA-87 (NIST Level 5)
- **Performance**: ML-KEM-512 + ML-DSA-44 (NIST Level 1)

### **Cryptographic Features**
- **Key Encapsulation Mechanisms** - Quantum-safe key exchange
- **Digital Signatures** - Non-repudiation and authentication
- **Hybrid Encryption** - Best of both cryptographic worlds
- **Algorithm Agility** - Easy algorithm swapping and upgrades

---

**Tech Stack Version**: 1.0  
**Last Updated**: August 1, 2025  
**Security Focus**: Post-Quantum Ready
