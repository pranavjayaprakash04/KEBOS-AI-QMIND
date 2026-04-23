from sqlalchemy import Column, Integer, String, Boolean, JSONB
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="ANALYST")
    tenant_id = Column(Integer, nullable=False)
    tenant_type = Column(String, default="enterprise")
    fido2_enabled = Column(Boolean, default=False, server_default='false')
    fido2_credentials = Column(JSONB, nullable=True, server_default='[]')
    totp_secret_encrypted = Column(String, nullable=True)
