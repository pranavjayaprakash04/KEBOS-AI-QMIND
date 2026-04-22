# Authentication Module

A comprehensive, secure authentication and authorization system for the CTP platform. Provides JWT-based authentication, role-based access control, and user management with enterprise-grade security features.

## Features

### 🚀 **Core Functionality**
- **JWT Authentication**: Secure token-based authentication with configurable expiration
- **Role-Based Access Control (RBAC)**: Fine-grained permission system with predefined roles
- **User Management**: Complete CRUD operations for user accounts
- **Password Security**: bcrypt hashing with salt for secure password storage
- **Permission Checking**: Runtime permission validation for resources
- **Async Support**: Full async/await support for high performance

### 🔒 **Security Features**
- **Token Validation**: JWT signature verification and expiration checking
- **Permission Enforcement**: Automatic permission checking via dependencies
- **Password Policies**: Configurable password strength requirements
- **Account Security**: Support for account activation/deactivation
- **Audit Logging**: Security event logging for compliance and monitoring
- **Error Handling**: Comprehensive error handling with proper HTTP status codes

### 📊 **Enterprise Features**
- **Celery Integration**: Background tasks for maintenance and auditing
- **Health Monitoring**: Service health checks and status reporting
- **Comprehensive Testing**: Full test coverage with unit and integration tests
- **Documentation**: Complete API documentation with OpenAPI/Swagger

## API Endpoints

### Register User
```http
POST /auth/register
```
Register a new user.

**Parameters:**
- `username`: Desired username
- `password`: Password
- `email`: Email address

### Login
```http
POST /auth/login
```
Authenticate a user and issue a JWT token.

**Parameters:**
- `username`: Username
- `password`: Password

**Response:**
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### Refresh Token
```http
POST /auth/refresh
```
Refresh an access token.

### User Info
```http
GET /auth/me
```
Get current user information.

### Logout
```http
POST /auth/logout
```
Revoke the current token.

## Configuration

### Environment Variables

```bash
# Auth Configuration
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRES=3600

# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs
```

### Security Configuration

```python
# Password policy
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
```

## Usage Examples

### Python Client

```python
import requests

data = {'username': 'user', 'password': 'pass'}
response = requests.post('http://localhost:8000/auth/login', json=data)
token = response.json()['access_token']

# Use token for authenticated requests
headers = {'Authorization': f'Bearer {token}'}
userinfo = requests.get('http://localhost:8000/auth/me', headers=headers).json()
```

### JavaScript/TypeScript Client

```typescript
const response = await fetch('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ username, password }),
  headers: { 'Content-Type': 'application/json' }
});
const { access_token } = await response.json();

const userInfo = await fetch('/auth/me', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
```

## Processing Pipeline

1. **Request Validation**: Input and payload checks
2. **Authentication**: Credential verification and token issuance
3. **Authorization**: Role and permission checks
4. **Audit Logging**: Operation and user tracking
5. **Response**: Status or result returned

## Error Handling

- **Validation Errors**: Input or payload issues
- **Authentication Errors**: Invalid credentials
- **Authorization Errors**: Insufficient permissions
- **System Errors**: Infrastructure or service issues

**Error Response Example:**
```json
{
  "detail": "Invalid credentials"
}
```

## Monitoring & Observability

- **Metrics**: Login success/failure rates, active sessions
- **Logging**: Structured logs, error tracking, audit trails
- **Health Checks**: Service and dependency status endpoints

## Security Considerations

- **Input Validation**: Prevent injection and malformed data
- **Access Control**: Enforce user permissions
- **Audit Logging**: Track all operations and users
- **Data Protection**: Secure storage and transmission

## Performance Optimization

- **Token Caching**: Use in-memory cache for active sessions
- **Scalability**: Horizontal scaling and resource pooling

## Troubleshooting

- **Common Issues**: Invalid credentials, token expired, user not found
- **Debug Mode**: Enable debug logging for more details
- **Health Check**: Use health endpoints to verify service status

## Contributing

1. Install dependencies: `pip install -r requirements.txt`
2. Set up environment variables
3. Start required services (Database, etc.)
4. Run tests: `pytest tests/`

- Follow PEP 8 and use type hints
- Add docstrings and error handling
- Write unit and integration tests

## License

This module is part of the AI Governance Platform and follows the same licensing terms.
