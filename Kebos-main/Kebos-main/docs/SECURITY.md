# Security Guidelines for Cyber Threat Platform

## Overview
This document outlines the security measures implemented in the Cyber Threat Platform and provides guidance for secure deployment and operation.

## Critical Security Fixes Implemented

### 1. Environment Variable Security
- **Issue Fixed**: Hardcoded secret key fallback
- **Solution**: Environment variable validation with no fallbacks
- **Action Required**: Set `SECRET_KEY` environment variable with a strong key

### 2. CORS Configuration
- **Issue Fixed**: Overly permissive CORS (`allow_origins=["*"]`)
- **Solution**: Configurable allowed origins via `ALLOWED_ORIGINS`
- **Action Required**: Configure `ALLOWED_ORIGINS` for your deployment

### 3. File Upload Security
- **Issue Fixed**: Path traversal vulnerabilities
- **Solution**: Comprehensive filename validation and sanitization
- **Features**: File type validation, size limits, character sanitization

### 4. Database Security
- **Issue Fixed**: Missing transaction rollback and session management
- **Solution**: Proper transaction handling with rollback on errors
- **Features**: Automatic cleanup on failures

### 5. Input Validation
- **Issue Fixed**: Generic exception handling
- **Solution**: Specific validation with proper error messages
- **Features**: Pydantic validators, input sanitization

## Required Environment Variables

### Critical (Must be set)
```bash
# Security
SECRET_KEY=your-super-secret-key-here-change-this-in-production

# Database
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=your_db_host
POSTGRES_PORT=5432
POSTGRES_DB=your_db_name

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Optional (Recommended)
```bash
# Logging
LOG_LEVEL=INFO
LOG_DIR=./logs

# File Upload
MODEL_UPLOAD_DIR=./uploads

# Frontend
REACT_APP_API_URL=http://localhost:8000
```

## Security Best Practices

### 1. Secret Key Generation
Generate a secure secret key:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### 2. Database Security
- Use strong, unique passwords
- Restrict database access to application servers only
- Enable SSL/TLS for database connections
- Regular security updates

### 3. Network Security
- Use HTTPS in production
- Configure firewall rules
- Implement rate limiting
- Monitor access logs

### 4. File Upload Security
- Validate file types and sizes
- Scan uploaded files for malware
- Store files outside web root
- Implement access controls

### 5. Application Security
- Regular dependency updates
- Security headers implementation
- Input validation and sanitization
- Error handling without information disclosure

## Deployment Checklist

### Pre-deployment
- [ ] Generate secure SECRET_KEY
- [ ] Configure ALLOWED_ORIGINS
- [ ] Set up secure database credentials
- [ ] Configure HTTPS certificates
- [ ] Set up monitoring and logging

### Post-deployment
- [ ] Test all security endpoints
- [ ] Verify CORS configuration
- [ ] Check file upload restrictions
- [ ] Validate error handling
- [ ] Monitor security logs

## Security Headers

The application includes the following security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'self'`

## Vulnerability Reporting

If you discover a security vulnerability, please:
1. **Do not** create a public issue
2. Email security@yourdomain.com
3. Include detailed reproduction steps
4. Allow time for assessment and fix

## Regular Security Maintenance

### Weekly
- Review application logs
- Check for dependency updates
- Monitor failed login attempts

### Monthly
- Security dependency audit
- Review access controls
- Update security documentation

### Quarterly
- Security penetration testing
- Review and update security policies
- Staff security training

## Security Standards

### Industry Best Practices
- Zero-trust architecture
- Defense in depth
- Least privilege access
- Continuous monitoring

### Security Frameworks
- Access controls
- Change management
- Incident response
- Risk assessment

### ISO 27001
- Information security management
- Risk assessment
- Security controls
- Continuous improvement

## Emergency Response

### Security Incident Response Plan
1. **Identify**: Detect and classify the incident
2. **Contain**: Isolate affected systems
3. **Eradicate**: Remove the threat
4. **Recover**: Restore normal operations
5. **Learn**: Document lessons learned

### Contact Information
- Security Team: security@yourdomain.com
- Emergency: +1-XXX-XXX-XXXX
- Incident Response: incident@yourdomain.com

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/) 