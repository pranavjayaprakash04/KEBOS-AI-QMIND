# Job Manager Module

A robust, production-ready job management system for the AI Governance Platform. Handles scheduling, tracking, and management of asynchronous and batch jobs across all platform modules.

## Features

### 🚀 **Core Functionality**
- **Job Scheduling**: Schedule and manage Celery tasks and batch jobs
- **Progress Tracking**: Real-time status and progress updates for jobs
- **Job Metadata**: Store and query job parameters, results, and logs
- **Audit Logging**: Complete audit trail for all job operations

### 🔒 **Security Features**
- **Input Validation**: Strict validation of job parameters
- **Access Control**: User-based access control and audit trails
- **Error Handling**: Standardized error responses and logging

### 📊 **Monitoring & Analytics**
- **Job Analytics**: Track job success/failure rates and durations
- **Health Checks**: Service health monitoring

## API Endpoints

### Submit Job
```http
POST /job_manager/submit
```
Submit a new job for processing.

### Job Status
```http
GET /job_manager/status/{job_id}
```
Get real-time status of a job.

### Job Results
```http
GET /job_manager/results/{job_id}
```
Retrieve results for a completed job.

### List Jobs
```http
GET /job_manager/jobs
```
List all jobs with filtering and pagination.

## Configuration

### Environment Variables

```bash
# Job Manager Configuration
JOB_MANAGER_MAX_CONCURRENT=10

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
```

## Usage Examples

### Python Client

```python
import requests

data = {'task': 'model_upload', 'parameters': {...}}
response = requests.post('http://localhost:8000/job_manager/submit', json=data)
job_id = response.json()['job_id']

# Check status
status = requests.get(f'http://localhost:8000/job_manager/status/{job_id}').json()
```

## Processing Pipeline

1. **Request Validation**: Input and payload checks
2. **Job Scheduling**: Async job creation and tracking
3. **Job Execution**: Main job logic (delegated to module)
4. **Result Storage**: Database and/or external service update
5. **Audit Logging**: Operation and user tracking
6. **Response**: Status or result returned

## Error Handling

- **Validation Errors**: Input or payload issues
- **Processing Errors**: Internal or dependency failures
- **System Errors**: Infrastructure or service issues

## Monitoring & Observability

- **Metrics**: Job success/failure rates, processing times
- **Logging**: Structured logs, error tracking, audit trails
- **Health Checks**: Service and dependency status endpoints

## Security Considerations

- **Input Validation**: Prevent injection and malformed data
- **Access Control**: Enforce user permissions
- **Audit Logging**: Track all operations and users
- **Data Protection**: Secure storage and transmission

## Performance Optimization

- **Asynchronous Processing**: Use Celery for heavy tasks
- **Batch Operations**: Support for bulk job submission
- **Scalability**: Horizontal scaling and resource pooling

## Troubleshooting

- **Common Issues**: Invalid parameters, job not found, job fails
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
