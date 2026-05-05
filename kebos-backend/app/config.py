from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/kebos"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "user"
    DB_PASSWORD: str = "pass"
    DB_NAME: str = "kebos"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    
    # Vault
    VAULT_ADDR: str = "http://localhost:8200"
    VAULT_TOKEN: str = ""
    VAULT_KV_MOUNT: str = "secret"  # KV v2 mount point
    VAULT_ENABLED: bool = False     # True in production
    VAULT_DEV_FERNET_KEY: str = ""  # Dev-only fallback encryption key
    VAULT_PKI_ENABLED: bool = True
    VAULT_DEV_RSA_PRIVATE_KEY: str = ""
    
    # JWT
    JWT_ALGORITHM: str = "RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 480
    
    # PQC
    USE_REAL_PQC: bool = True

    # Security
    SECRET_KEY: str = ""
    
    # Syslog
    POSTGRES_USER: str = "kebos"
    POSTGRES_PASSWORD: str = "kebos_password"
    POSTGRES_DB: str = "kebos"
    SYSLOG_HOST: str = ""
    SYSLOG_PORT: int = 6514
    SYSLOG_CA_CERT: str = ""
    
    # Splunk HEC
    SPLUNK_HEC_URL: str = ""
    SPLUNK_HEC_TOKEN: str = ""
    SPLUNK_INDEX: str = "kebos"
    
    # CORS
    CORS_ORIGINS: list = [
        "https://app.kebos.in",
        "http://localhost:5173",
    ]
    
    # Egress Control
    EGRESS_STRICT_MODE: bool = True
    ALLOWED_EGRESS_DOMAINS: list = [
        "certstream.calidog.io",
        "api.groq.com",
        "api.abuseipdb.com",
        "api.feodotracker.abuse.ch",
        "api.malwarebazaar.com",
        "nvd.nist.gov",
        "openphish.com",
        "data.phishtank.org",
        "urlhaus-api.abuse.ch",
        "tranco-list.eu",
        "whoisxmlapi.com",
        "pastebin.com",
        "abuse.ch",
        "virustotal.com",
        "otx.alienvault.com",
        "threatconnect.com",
        "misp.example.com",
        "api.crowdstrike.com",
        "firehose.example.com",
        "api.shodan.io",
        "vault.local",
        "localhost",
    ]
    
    # API Keys
    WHOISXML_API_KEY: str = ""
    
    # Zeek Log Monitoring
    ZEEK_ENABLED: bool = False
    ZEEK_LOG_DIR: str = "/opt/zeek/logs/current/"

    # GeoIP
    GEOIP_DB_PATH: str = "data/GeoLite2-City.mmdb"  # path to GeoLite2-City.mmdb

    # FIDO2/WebAuthn
    FIDO2_RP_ID: str = "kebos.in"
    FIDO2_RP_NAME: str = "Kebos AI"

    # LLM / GenAI
    GROQ_API_KEY: str = ""
    LOCAL_GEMMA_URL: str = "http://localhost:11434"

    # CERT-In Report Signing
    DILITHIUM_SIGNING_KEY_HEX: str = ""   # load from Vault in production

    class Config:
        env_file = ".env"


settings = Settings()
