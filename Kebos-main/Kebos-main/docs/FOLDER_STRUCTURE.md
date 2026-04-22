# KEBOS Folder Structure

## Production Folders

### `/backend`
- Core backend application code
- FastAPI application with modular services
- **Active Services:**
  - `genai_assistant/` - GenAI service using Gemma LLM
  - `auth/` - Authentication and authorization
  - `audit_logger/` - Audit logging service
  - `common/` - Shared utilities and models
  - `job_manager/` - Background job management
  - `messaging/` - Message handling
  - `network_analytics/` - Network analysis
  - `siem_integration/` - SIEM integration
  - `threat_detection/` - Threat detection algorithms

### `/frontend`
- React/Vite frontend application
- Modern UI using TypeScript and Tailwind CSS

### `/notebooks`
- Jupyter notebooks for data science and ML experiments
- CatBoost models and analysis
- Anomaly detection research

## Organization Folders

### `/archive`
- **`/reports`** - Old reports and documentation
- **`/diagrams`** - Flow diagrams and architecture docs
- **`/unused_frontend`** - Legacy frontend code
- **`logs`** - Old log files
- **`messaging_storage`** - Legacy message storage
- **`secure_messages`** - Legacy secure messaging

### `/tests`
- **`/backend`** - Backend unit and integration tests
- **`/integration`** - Cross-service integration tests

### `/utils`
- **Configuration files:** `alembic.ini`, `env.example`, `Makefile`
- **Development utilities and helper scripts**

### `/docs`
- **`/deployment`** - Deployment guides and checklists
- **`/features`** - Feature documentation
- **Main documentation files**

### `/scripts`
- **Deployment scripts:** `deploy.sh`, `verify-deployment.sh`, `final-deployment-checklist.sh`
- **Integration scripts:** `integrate-model.py`

## Key Changes Made

1. **LLM Migration**: Replaced Mixtral with Gemma (lightweight model)
2. **Code Organization**: Moved all non-essential files to appropriate folders
3. **Test Organization**: Consolidated all test files in `/tests` folder
4. **Documentation**: Organized all docs in `/docs` with subfolders
5. **Archive**: Preserved all legacy code and reports in `/archive`

## Production Ready Structure

The main folders (`backend`, `frontend`, `notebooks`) now contain only production-ready code:
- ✅ Clean, maintainable codebase
- ✅ Proper separation of concerns
- ✅ All tests organized separately
- ✅ Documentation properly structured
- ✅ Legacy code archived (not deleted)

## Next Steps

1. Update any import paths if needed
2. Update CI/CD pipelines to reflect new structure
3. Update documentation references
4. Test deployment with new structure
