
# Audit Logger Module

A comprehensive, production-ready audit logging system for the AI Governance Platform. Handles logging of all critical operations, user actions, and system events for traceability and compliance.

## Features

### 🚀 **Core Functionality**
- **Centralized Logging**: Captures logs from all platform modules
- **Structured Logs**: JSON and context-rich log entries
- **Asynchronous Processing**: Uses Celery for log processing and storage
- **Searchable Audit Trail**: Query and filter logs by user, action, or resource
- **Integration**: Works with external SIEM and monitoring tools

### 🔒 **Security Features**
- **Tamper-Resistant Storage**: Write-once, append-only log storage
- **Access Control**: Role-based access to logs
- **Input Validation**: Strict validation of log entries
- **Error Handling**: Standardized error responses and logging

### 📊 **Monitoring & Analytics**
- **Log Analytics**: Aggregation and statistics on log events
- **Health Checks**: Service and storage monitoring

## API Endpoints

### Log Event
```http
POST /audit_logger/log
```
Log a new event or action.

**Parameters:**
- `user_id`: User performing the action
- `action`: Action type
- `resource`: Resource affected
- `details`: Additional context

**Response:**
```json
{
  "status": "logged",
  "log_id": "log-uuid"
}
```

### Search Logs
```http
GET /audit_logger/logs
```
Query logs with filters and pagination.

**Query Parameters:**
- `user_id`, `action`, `resource`, `from`, `to`, `limit`, `offset`

### Log Details
```http
GET /audit_logger/logs/{log_id}
```
Retrieve details for a specific log entry.

## Configuration

### Environment Variables

```bash
# Audit Logger Configuration
AUDIT_LOGGER_STORAGE=./logs/audit.log

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
```

### Security Configuration

```python
# Input validation
MAX_ACTION_LENGTH = 100
MAX_RESOURCE_LENGTH = 100
MAX_DETAILS_SIZE = 10000
```

## Usage Examples

### Python Client

```python
import requests

data = {
    'user_id': 1,
    'action': 'model_upload',
    'resource': 'model/123',
    'details': 'Uploaded new model version.'
}
response = requests.post('http://localhost:8000/audit_logger/log', json=data)
log_id = response.json()['log_id']
```

### JavaScript/TypeScript Client

```typescript
const response = await fetch('/audit_logger/log', {
  method: 'POST',
  body: JSON.stringify(data),
  headers: { 'Content-Type': 'application/json' }
});
const result = await response.json();
const logId = result.log_id;
```

## Processing Pipeline

1. **Request Validation**: Input and payload checks
2. **Log Storage**: Write log entry to storage
3. **Audit Logging**: Operation and user tracking
4. **Response**: Status or result returned

## Error Handling

- **Validation Errors**: Input or payload issues
- **Processing Errors**: Storage or dependency failures
- **System Errors**: Infrastructure or service issues

**Error Response Example:**
```json
{
  "status": "failed",
  "error": "Invalid log details"
}
```

## Monitoring & Observability

- **Metrics**: Log volume, error rates
- **Logging**: Structured logs, error tracking, audit trails
- **Health Checks**: Service and storage status endpoints

## Security Considerations

- **Input Validation**: Prevent injection and malformed data
- **Access Control**: Enforce user permissions
- **Audit Logging**: Track all operations and users
- **Data Protection**: Secure storage and transmission

## Performance Optimization

- **Asynchronous Processing**: Use Celery for heavy tasks
- **Batch Operations**: Support for bulk log ingestion
- **Scalability**: Horizontal scaling and resource pooling

## Troubleshooting

- **Common Issues**: Invalid log data, storage full, log not found
- **Debug Mode**: Enable debug logging for more details
- **Health Check**: Use health endpoints to verify service status

## Contributing

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables
3. Start required services (Redis, Database, etc.)
4. Run tests: `pytest tests/`

- Follow PEP 8 and use type hints
- Add docstrings and error handling
- Write unit and integration tests

## License

This module is part of the AI Governance Platform and follows the same licensing terms.
