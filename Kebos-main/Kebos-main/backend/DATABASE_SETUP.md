# PostgreSQL Database Setup Guide

This guide will help you set up PostgreSQL for the AIGP (AI Governance Platform) application.

## Prerequisites

- Python 3.8+
- PostgreSQL 12+ installed and running
- pip (Python package manager)

## 1. Install PostgreSQL

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### macOS (using Homebrew)
```bash
brew install postgresql
brew services start postgresql
```

### Windows
Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

## 2. Create Database and User

Connect to PostgreSQL as the postgres user:

```bash
sudo -u postgres psql
```

Create the database and user:

```sql
-- Create database
CREATE DATABASE aigp_database;

-- Create user
CREATE USER aigp_user WITH PASSWORD 'secure_password_here';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE aigp_database TO aigp_user;

-- Connect to the database
\c aigp_database

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO aigp_user;

-- Exit
\q
```

## 3. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Copy the example environment file:

```bash
cp env.example .env
```

Edit `.env` with your PostgreSQL credentials:

```bash
# PostgreSQL Configuration
POSTGRES_USER=aigp_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=aigp_database

# Application Configuration
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

## 5. Initialize Database

### Option A: Using the initialization script
```bash
python init_db.py
```

### Option B: Using Alembic migrations
```bash
# Create initial migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### Option C: Using the migration script
```bash
python migrate_db.py
```

## 6. Verify Setup

Test the database connection:

```bash
python -c "
from common.db import engine
with engine.connect() as conn:
    result = conn.execute('SELECT version();')
    print(f'Connected to: {result.scalar()}')
"
```

## 7. Docker Setup (Alternative)

If you prefer using Docker:

```bash
# Copy environment file
cp env.example .env

# Start services
docker-compose up -d

# Initialize database
docker-compose exec backend python init_db.py
```

## 8. Database Schema

The application creates the following main tables:

### Common Models
- `audit_logs` - System audit trail
- `robustness_logs` - Model robustness tracking
- `security_events` - Security incident logging

### GovernCore Models
- `governance_checklists` - Governance checklist templates
- `governance_checklist_items` - Individual checklist items
- `governance_evidence_records` - Evidence for checklist items
- `governance_oversight_logs` - Oversight activity logs

### Model Ingestor Models
- `uploaded_models` - Model metadata and tracking
- `model_versions` - Model version history
- `model_artifacts` - Model artifacts and files

## 9. Troubleshooting

### Connection Issues
```bash
# Test PostgreSQL connection
psql -h localhost -U aigp_user -d aigp_database

# Check PostgreSQL status
sudo systemctl status postgresql
```

### Permission Issues
```bash
# Fix PostgreSQL authentication
sudo nano /etc/postgresql/*/main/pg_hba.conf
# Add: local aigp_database aigp_user md5
sudo systemctl restart postgresql
```

### Migration Issues
```bash
# Reset migrations
alembic downgrade base
alembic upgrade head

# Check migration status
alembic current
alembic history
```

## 10. Production Considerations

### Security
- Use strong passwords
- Enable SSL connections
- Restrict network access
- Regular backups

### Performance
- Configure connection pooling
- Optimize PostgreSQL settings
- Monitor query performance
- Regular maintenance

### Backup
```bash
# Create backup
pg_dump -h localhost -U aigp_user aigp_database > backup.sql

# Restore backup
psql -h localhost -U aigp_user aigp_database < backup.sql
```

## 11. Monitoring

### Check Database Size
```sql
SELECT pg_size_pretty(pg_database_size('aigp_database'));
```

### Check Active Connections
```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'aigp_database';
```

### Check Table Sizes
```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Support

If you encounter issues:

1. Check the logs: `tail -f /var/log/postgresql/postgresql-*.log`
2. Verify environment variables: `env | grep POSTGRES`
3. Test connection manually: `psql -h localhost -U aigp_user -d aigp_database`
4. Check application logs for specific error messages 