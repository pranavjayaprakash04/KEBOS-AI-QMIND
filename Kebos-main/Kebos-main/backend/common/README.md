# Common Module

A shared utility and infrastructure module for the Cyber Threat Platform. Provides database connections, Celery app, common models, logging, and reusable utilities for all backend modules.

## Features

### 🚀 **Core Functionality**
- **Database Utilities**: SQLAlchemy session management and migrations
- **Celery App**: Centralized Celery configuration for async tasks
- **Common Models**: Shared Pydantic and SQLAlchemy models
- **Logging Utilities**: Structured and audit logging helpers
- **Reusable Functions**: Utilities for validation, error handling, and more

### 🔒 **Security Features**
- **Input Validation**: Shared validators for all modules
- **Audit Logging**: Centralized logging for compliance
- **Error Handling**: Standardized error responses and logging

### 📊 **Monitoring & Analytics**
- **Health Checks**: Database and Celery connectivity
- **Logging**: Centralized log management

## API Endpoints

This module is not intended to expose direct API endpoints, but provides shared code for other modules.

## Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:pass@db:5432/ctp

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
```

## Usage Examples

### Python Example

```python
from common.db import get_db_session
from common.celery_app import celery_app

# Use shared DB session
with get_db_session() as session:
    ...

# Use shared Celery app
def my_task():
    ...
celery_app.task(my_task)
```

## Processing Pipeline

1. **Initialization**: Load configuration and initialize shared resources
2. **Usage**: Import and use utilities in other modules
3. **Logging**: Centralized logging for all modules

## Error Handling

- **Validation Errors**: Input or payload issues
- **System Errors**: Infrastructure or service issues

## Monitoring & Observability

- **Health Checks**: Database and Celery status
- **Logging**: Structured logs, error tracking

## Security Considerations

- **Input Validation**: Prevent injection and malformed data
- **Audit Logging**: Track all operations and users
- **Data Protection**: Secure storage and transmission

## Performance Optimization

- **Connection Pooling**: Efficient DB and Celery resource usage
- **Scalability**: Shared infrastructure for all modules

## Troubleshooting

- **Common Issues**: DB connection errors, Celery misconfiguration
- **Debug Mode**: Enable debug logging for more details
- **Health Check**: Use health endpoints in dependent modules

## Contributing

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables
3. Start required services (Database, Redis, etc.)
4. Run tests: `pytest tests/`

- Follow PEP 8 and use type hints
- Add docstrings and error handling
- Write unit and integration tests

## License

This module is part of the Cyber Threat Platform and follows the same licensing terms.
