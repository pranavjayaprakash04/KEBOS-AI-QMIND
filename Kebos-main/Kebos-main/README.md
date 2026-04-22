# Cyber Threat Platform (CTP) Monorepo

This monorepo contains all services and modules for a real-time cyber threat prediction and mitigation platform, including:
- Threat Detection Engine (real-time anomaly detection)
- SIEM Integration (external SIEM API integration)
- Network Analytics (streaming data processing)  
- Threat Intelligence (GenAI-powered threat analysis)
- Security Monitoring (audit logging and alerting)
- Auth (OAuth2, RBAC, zero-trust)
- Threat Dashboard (React with real-time updates)

## Structure
 - `/backend` — FastAPI, Celery, Kafka, streaming modules
 - `/frontend` — React + Vite with WebSocket support
 - `/docker` — Docker Compose, Kafka, TimescaleDB

# Cyber Threat Platform (CTP) Monorepo

This monorepo contains all services and modules for a real-time cyber threat prediction and mitigation platform, including:
- **Threat Detection Engine** (real-time anomaly detection with autoencoder neural networks)
- **SIEM Integration** (external SIEM API integration with webhook support)
- **Network Analytics** (streaming data processing with Apache Kafka and Flink)  
- **Threat Intelligence** (GenAI-powered threat analysis with RAG architecture)
- **Security Monitoring** (comprehensive audit logging and alerting)
- **Auth** (OAuth2, RBAC, zero-trust security architecture)
- **Threat Dashboard** (React with real-time WebSocket updates)

## 🏗️ Architecture Overview

The CTP follows a **microservices-based architecture** designed for scalability, security, and real-time performance:

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Ingestion│───▶│  Stream Processing│───▶│  AI/ML Engine   │
│   & Streaming   │    │   & Analytics     │    │  & Detection    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  TimescaleDB    │    │     Kafka        │    │  GenAI Assistant│
│  (Time-series)  │    │  (Message Bus)   │    │   (RAG-based)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd cyber-threat-platform
cp .env.ctp.example .env
```

### 2. Configure Environment
Edit `.env` file with your specific configurations:
```bash
# Essential configurations
POSTGRES_PASSWORD=your_secure_password
SECRET_KEY=your_super_secret_key
LLM_API_ENDPOINT=http://localhost:11434
```

### 3. Start the Platform
```bash
# Start all services with Docker Compose
docker-compose -f docker-compose.ctp.yml up -d

# Or use npm scripts
npm run docker:up
```

### 4. Access the Platform
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Kafka UI**: http://localhost:9000
- **TimescaleDB**: localhost:5432

## 🏛️ System Architecture

### Zero-Trust Security Model
- **mTLS**: All inter-service communication encrypted
- **JWT Authentication**: Stateless authentication with refresh tokens
- **RBAC**: Role-based access control
- **API Gateway**: Rate limiting, authentication, and routing

### Multi-Layer AI Strategy

#### Layer 1: Real-Time Anomaly Detection
- **Autoencoder Neural Networks** on streaming data
- **<50ms detection latency** for real-time threat identification
- **Statistical baseline analysis** for rapid anomaly flagging

#### Layer 2: Advanced Threat Prediction
- **Fine-tuned Transformer models** on cybersecurity datasets
- **MITRE ATT&CK framework** integration
- **Narrative threat descriptions** with confidence scoring

#### Layer 3: Context-Aware GenAI Assistant
- **RAG Architecture** for grounded responses
- **Real-time data retrieval** from TimescaleDB and SIEM logs
- **Natural language querying** of security incidents

### Data Pipeline Architecture

```
Network Packets ──▶ Kafka (raw_packets) ──▶ Flink Processing ──▶ TimescaleDB
      │                     │                        │               │
      │                     ▼                        ▼               ▼
SIEM Events ──────▶ Kafka (siem_events) ─▶ Threat Analysis ─▶ Alert Generation
      │                     │                        │               │
      │                     ▼                        ▼               ▼
Threat Intel ─────▶ Kafka (threat_alerts) ▶ GenAI Assistant ▶ Dashboard Updates
```

## 📦 Project Structure

```
cyber-threat-platform/
├── backend/                    # FastAPI backend services
│   ├── threat_detection/       # Core threat detection engine
│   ├── siem_integration/       # SIEM API integration
│   ├── network_analytics/      # Streaming analytics
│   ├── genai_assistant/        # RAG-based AI assistant
│   ├── auth/                   # Authentication & authorization
│   ├── audit_logger/           # Security audit logging
│   ├── job_manager/            # Background job management
│   └── common/                 # Shared utilities
├── frontend/                   # React dashboard
│   ├── src/components/         # UI components
│   ├── src/pages/              # Dashboard pages
│   ├── src/services/           # API services
│   └── src/websocket/          # Real-time updates
├── docker/                     # Docker configurations
├── docs/                       # Documentation
└── scripts/                    # Deployment scripts
```

## 🔧 Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
cd backend
python -m pytest
```

## 🚨 Key Features

### Real-Time Threat Detection
- **1000+ packets/sec** processing capability
- **Multi-layer AI analysis** with autoencoder and transformer models
- **MITRE ATT&CK** technique mapping
- **False positive rate <5%** with continuous model tuning

### Advanced Analytics
- **Time-series analysis** of network traffic patterns
- **Geolocation enrichment** for threat attribution
- **Correlation engine** for multi-event threat scenarios
- **Predictive modeling** for threat trend analysis

### SIEM Integration
- **Universal API support** for major SIEM platforms
- **Webhook endpoints** for real-time event ingestion
- **Normalized event format** across different SIEM vendors
- **Bidirectional sync** for alert enrichment

### Zero-Trust Security
- **Service mesh** with Istio for mTLS
- **API Gateway** with OAuth2 and rate limiting
- **Encrypted data at rest** with AES-256
- **Comprehensive audit trails** for compliance

## 🔌 API Endpoints

### Threat Detection
```
POST /threats/detect           # Single packet analysis
POST /threats/batch-detect     # Batch packet processing
GET  /threats/alerts           # Historical alerts
GET  /threats/stats            # Detection statistics
WS   /threats/alerts/stream    # Real-time alert stream
```

### SIEM Integration
```
POST /siem/configure           # Configure SIEM connection
POST /siem/webhook             # SIEM webhook endpoint
GET  /siem/health              # SIEM connection health
GET  /siem/events              # Query SIEM events
```

### GenAI Assistant
```
POST /assistant/query          # Natural language queries
WS   /assistant/chat           # Real-time chat interface
GET  /assistant/context        # Current context state
POST /assistant/feedback       # Model feedback
```

## 🔍 Monitoring & Observability

### Metrics & Alerts
- **Prometheus metrics** for system monitoring
- **Custom dashboards** for threat visibility
- **Automated alerting** for system health
- **Performance tracking** for SLA compliance

### Health Checks
- **Service health endpoints** for all components
- **Database connectivity** monitoring
- **Kafka cluster health** tracking
- **AI model performance** metrics

## 🛡️ Security Considerations

### Data Protection
- **End-to-end encryption** for all data flows
- **Data retention policies** for compliance
- **PII scrubbing** in log data
- **Secure credential management**

### Network Security
- **Network segmentation** for service isolation
- **Firewall rules** for service communication
- **VPN access** for administrative tasks
- **Intrusion detection** on the platform itself

## 📊 Performance Specifications

### Latency Requirements
- **Threat Detection**: <50ms per packet
- **Alert Generation**: <100ms end-to-end
- **Dashboard Updates**: <200ms via WebSocket
- **API Response**: <500ms for complex queries

### Throughput Capacity
- **Network Packets**: 1000+ packets/second
- **SIEM Events**: 500+ events/second
- **Concurrent Users**: 100+ dashboard users
- **API Requests**: 1000+ requests/minute

## 🚀 Deployment

### Production Deployment
```bash
# Production environment
docker-compose -f docker-compose.ctp.yml -f docker-compose.prod.yml up -d

# With SSL certificates
./scripts/setup-ssl.sh
./scripts/deploy-production.sh
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/services/
kubectl apply -f k8s/deployments/
```

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [API Reference](docs/api-reference.md)
- [Architecture Deep Dive](docs/architecture.md)
- [Security Best Practices](docs/security.md)
- [Troubleshooting Guide](docs/troubleshooting.md)

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Open a GitHub issue for bugs or feature requests
- **Security**: Report security vulnerabilities privately to security@yourcompany.com

---

**Built with ❤️ for cybersecurity professionals**

---

## 📁 Directory Structure
 - `/backend` — FastAPI, Celery, SQLAlchemy, modular feature folders (see below)
 - `/frontend` — React + Vite dashboard
 - `/docker` — Docker Compose, Dockerfiles
 - `/.env.example` — Environment variable template
 - `/Makefile` — Common dev commands
 - `/.devcontainer` — VS Code DevContainer config

---

## 🚀 Quickstart (Local Dev)
1. **Clone the repo** and `cd` into the root directory.
2. **Copy environment variables:**
   ```sh
   cp .env.example .env
   # Edit .env as needed
   ```
3. **Start all services with Docker Compose:**
   ```sh
   docker compose up --build
   ```
4. **Access the platform:**
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
   - MLflow UI: [http://localhost:5000](http://localhost:5000)

---

## 🛠️ Backend Modules
- **govercore**: Model upload, metadata, MLflow registry
- **docgen**: Model cards, risk/compliance docs (LLM-powered)
- **explainx**: Explainability (SHAP, LIME)
- **biasaudit**: Bias/fairness audits (AIF360, Fairlearn)
- **attacksim**: Adversarial testing (ART, Foolbox)
- **promptshield**: LLM prompt security
- **auth**: OAuth2, RBAC, team invites
- **common**: Shared code, DB, Celery, utils

Each module exposes its own API routes (see `/docs`).

---

## 🖥️ Frontend Dashboard
 - Located in `/frontend`
 - Built with React, Vite
 - Role-based dashboard for Dev, Auditor, Admin

---

## 🐳 DevOps & Tooling
- **Docker Compose**: Orchestrates all services
- **Makefile**: Common commands (`up`, `down`, `lint`, `format`, etc.)
- **DevContainer**: VS Code remote dev support

---

## 🧪 Testing
- Backend: `pytest` or FastAPI's `TestClient`
- Frontend: `npm test` (if tests are added)

---

## 🔗 API Documentation
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧠 Extending the Platform
- Add new modules under `/backend`
- Use Pydantic, SQLAlchemy, and FastAPI best practices
- All services are API-first and designed for extensibility

---

## 🛡️ Security & Best Practices
- OAuth2 login, RBAC, and team invites
- Secure API endpoints and handle errors gracefully
- Use `.env` for secrets (never commit real secrets)

---

## 📬 Support
For questions, see module READMEs or contact the maintainers.

---

Happy governing! 🚦

Create a default Unix user account: madhu
New password:
Retype new password:
12dd3360-877b-4f87-aa0f-81f4c43cac95"# AIGP" 
#   K e b o s  
 