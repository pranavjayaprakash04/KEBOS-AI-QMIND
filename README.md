# KebosAI QUMIND - Production-Grade Threat Intelligence Platform

## Overview

KebosAI QUMIND is a production-grade threat intelligence platform with:
- **Phase 1**: Auth Hardening (RS256 JWT, HttpOnly cookies, TOTP MFA, Vault encryption)
- **Phase 2**: QMind Integration (10-category probabilistic engine, supplier trust, signal decay)
- **Phase 3**: Egress Control (domain whitelist, 10s timeout)
- **Phase 4**: Deception Grid (Honeytokens, SIEM integration with CEF/STIX)

## Architecture

### Services

| Service | Port | Description |
|---------|------|-------------|
| kebos-backend | 8000 | FastAPI backend with auth, threat detection, honeygrid |
| qmind-enterprise | 8001 | QMind probabilistic signal engine with PQC |
| postgresql | 5432 | PostgreSQL 16 + TimescaleDB |
| redis | 6379 | Redis for caching and JTI blacklist |
| kafka | 9092 | Kafka for message streaming |
| zookeeper | 2181 | ZooKeeper for Kafka coordination |
| vault | 8200 | HashiCorp Vault for secret management |
| influxdb | 8086 | InfluxDB for time-series metrics |
| docker-proxy | 2375 | Tecnativa docker-proxy (Bug fix #9) |

### Networks

- `frontend-net`: Frontend to backend communication
- `app-net`: Internal service communication
- `data-net`: Database and cache access

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11 (backend)
- Python 3.12 (qmind-enterprise)
- Node.js 18+ (frontend)

### Start All Services

```bash
docker-compose up --build -d
```

### Health Checks

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### Stop Services

```bash
docker-compose down
```

## Backend (kebos-backend)

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://kebos:kebos_password@postgres:5432/kebos

# Redis
REDIS_URL=redis://redis:6379

# Vault
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=dev-only-token

# Auth
SECRET_KEY=change-me-in-production
JWT_ALGORITHM=RS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# PQC
USE_REAL_PQC=true

# Syslog (SIEM)
SYSLOG_HOST=siem.local
SYSLOG_PORT=6514
SYSLOG_CA_CERT=/path/to/ca.crt

# Egress Control
ALLOWED_EGRESS_DOMAINS=abuse.ch,virustotal.com,otx.alienvault.com,...
```

### API Endpoints

#### Auth
- `POST /api/v1/auth/login` - Login with HttpOnly cookie
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/logout` - Logout with JTI blacklist
- `POST /api/v1/auth/totp/enable` - Enable TOTP (TODO)
- `POST /api/v1/auth/verify-totp` - Verify TOTP (TODO)
- `POST /api/v1/auth/fido2/register/begin` - FIDO2 registration begin (TODO)
- `POST /api/v1/auth/fido2/register/complete` - FIDO2 registration complete (TODO)
- `POST /api/v1/auth/fido2/authenticate/begin` - FIDO2 auth begin (TODO)
- `POST /api/v1/auth/fido2/authenticate/complete` - FIDO2 auth complete (TODO)
- `POST /api/v1/auth/security/emergency-rotation` - Emergency secret rotation

#### Signals
- `POST /api/v1/signals/inject` - Inject threat signal (8 source types)
- `GET /api/v1/signals/sources` - List signal source types
- `GET /api/v1/signals/categories` - List threat categories

#### HoneyGrid
- `POST /api/v1/honeygrid/honeytokens` - Create honeytoken (ADMIN)
- `POST /api/v1/honeygrid/honeytokens/deploy` - Deploy honeytoken (ADMIN)
- `POST /api/v1/honeygrid/honeytokens/trigger` - Handle honeytoken trigger
- `GET /api/v1/honeygrid/honeytokens` - List honeytokens (ADMIN)
- `DELETE /api/v1/honeygrid/honeytokens/{id}` - Revoke honeytoken (ADMIN)

### Running Backend Locally

```bash
cd kebos-backend
pip install -r pyproject.toml
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
cd kebos-backend
pytest tests/ -x --tb=short
```

## QMind Enterprise (qmind-enterprise)

### Features

- **10-Category Probabilistic Engine**: C2_Infrastructure, Botnet_IP, Phishing, Malware, Credential_Leak, DDoS, Insider_Threat, Supply_Chain, CVE_Exploitation, Benign
- **Signal Decay**: India-calibrated λ values for 90+ day median dwell time
- **Supplier Trust Engine**: 8 external feeds with dynamic trust scoring
- **PQC**: Hybrid Kyber-768 + AES-256-GCM + Dilithium-3
- **Kafka Consumer**: aiokafka-based consumer (NEVER kafka-python)

### Kafka Topics

- `threat.indicators`: Kebos → QMind (CatBoost output)
- `qmind.results`: QMind → Kebos (MUST be consumed)
- `honeypot.interactions`: HoneyGrid → QMind
- `crawler.discoveries`: Crawlers → QMind
- `analyst.feedback`: UI → ML pipeline

### Running QMind Locally

```bash
cd qmind_enterprise
pip install -r requirements.txt
uvicorn enterprise_api:app --reload --host 0.0.0.0 --port 8001
```

## Frontend (kebos-frontend)

### Features

- React 18 + TypeScript + Vite
- Tailwind CSS for styling
- Zustand for state management
- HttpOnly cookie support (no localStorage)
- React Query for API calls

### Running Frontend Locally

```bash
cd kebos-frontend
npm install
npm run dev
```

## Security Features

### Auth Hardening (Phase 1)
- RS256 JWT with RSA-4096 keys
- HttpOnly+SameSite=Strict+Secure cookies
- Redis JTI blacklist for logout
- TOTP MFA with Vault transit encryption
- Government tenant FIDO2 enforcement
- Emergency secret rotation (<5 min target)
- Security headers on every response
- Environment validation at startup

### Egress Control (Phase 3)
- Domain whitelist (ALLOWED_EGRESS_DOMAINS)
- 10s timeout on all external calls
- EgressControlledClient wrapper for all outbound HTTP

### Deception (Phase 4)
- 3 honeytoken types: AWS keys, DB credentials, API tokens
- Tecnativa docker-proxy (Bug fix #9)
- SIEM integration via CEF format
- STIX 2.1 for threat intelligence

## Bug Fixes

- Bug #2: aiokafka throughout (NEVER kafka-python)
- Bug #3: done_callback on EVERY asyncio.create_task()
- Bug #4: qmind.results consumer running in Kebos backend at startup
- Bug #5: /signals/inject endpoint live, accepting all 8 source types
- Bug #9: Docker socket replaced by Tecnativa docker-proxy
- Bug #13: update_threat_with_qmind_result() fully implemented (NEVER a stub)

## Database Migrations

```bash
cd kebos-backend
alembic upgrade head
```

## Monitoring

### Metrics

- InfluxDB for time-series metrics
- Prometheus metrics (TODO)
- Grafana dashboards (TODO)

### Logging

- Structured JSON logging
- Syslog integration for SIEM
- CEF format for SIEM events
- STIX 2.1 for threat intelligence

## Development

### Project Structure

```
kebosAI_QUMIND/
├── kebos-backend/          # FastAPI backend
│   ├── app/
│   │   ├── auth/          # Auth services, router, dependencies
│   │   ├── deception/     # HoneyGrid manager
│   │   ├── integrations/  # Egress control
│   │   ├── security/      # Headers, validation, vault breach
│   │   ├── siem_integration/  # CEF + STIX formatters
│   │   ├── threat_detection/  # Signals router, QMind consumer
│   │   └── main.py        # FastAPI app
│   ├── alembic/           # Database migrations
│   ├── tests/             # Test suite
│   └── Dockerfile
├── qmind_enterprise/      # QMind probabilistic engine
│   ├── signal_engine/     # 10-category scorer
│   ├── feeds/             # Supplier trust engine
│   ├── pqc/               # Hybrid Kyber + Dilithium
│   ├── kafka_consumer.py  # aiokafka consumer
│   ├── enterprise_api.py   # FastAPI app
│   └── Dockerfile
├── kebos-frontend/       # React frontend
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── store/        # Zustand stores
│   │   ├── pages/        # React pages
│   │   └── components/   # React components
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml     # Multi-service orchestration
```

## License

Proprietary - KebosAI

## Support

For issues and questions, contact the KebosAI team.
