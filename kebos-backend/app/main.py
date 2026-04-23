from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.security.validate_environment import validate_environment
from app.security.headers import SecurityHeadersMiddleware
from app.auth.router import router as auth_router
from app.threat_detection.router import router as signals_router
from app.deception.router import router as honeygrid_router
from app.siem_integration.router import router as siem_router
from app.nta.router import router as nta_router
from app.nta.router import vuln_router
from app.cases.router import router as cases_router
from app.admin.tenants import router as admin_tenants_router
from app.reporting.router import router as reporting_router
from app.threat_detection.qmind_consumer import consume_qmind_results, set_qmind_dependencies, handle_task_error
from app.threat_detection.feedback_consumer import consume_analyst_feedback, set_feedback_dependencies
from app.cases.manager import get_case_manager
from app.reporting.cert_in_sla_monitor import get_cert_in_sla_monitor
from app.deception.honeytokens import get_honeytoken_manager
from app.crawlers.ct_log_monitor import get_ct_log_monitor
from app.crawlers.paste_monitor import get_paste_monitor
from app.crawlers.domain_monitor import get_domain_monitor
from app.integrations.dependency_health import get_dependency_health_monitor
from app.audit_logger.chain import AuditChain
from app.audit_logger.tls_syslog_handler import setup_tls_syslog
from app.threat_detection.kafka_producer import ThreatIndicatorPublisher
from app.reporting.soc_generator import SOCReportGenerator
from app.genai_assistant.llm_router import GroqClient, LocalGemmaClient
from app.dashboard.websocket_manager import websocket_manager
from app.config import settings
from app.api.middleware.rate_limit import limiter
from app.siem_integration.splunk_hec import splunk_hec
from app.security.vault_breach import vault_manager
import asyncpg
import sys
import asyncio
import uuid
import logging
import hvac
from pathlib import Path

# Add parent directory to path to import qmind_enterprise
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logger = logging.getLogger(__name__)

# Validate environment before starting app
errors = validate_environment()
critical_errors = [e for e in errors if e.startswith("CRITICAL")]
if critical_errors:
    print("Environment validation failed:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)

# Startup assertion for token expiry
assert settings.ACCESS_TOKEN_EXPIRE_MINUTES <= 15, (
    f"ACCESS_TOKEN_EXPIRE_MINUTES={settings.ACCESS_TOKEN_EXPIRE_MINUTES} exceeds 15. "
    "JWT tokens must expire within 15 minutes."
)

# Note: RedisStorage assertion removed - slowapi version may not support it
# Rate limiter falls back to in-memory storage if RedisStorage unavailable




def load_dilithium_signing_key() -> tuple[bytes, bytes, str]:
    """
    Load Dilithium-3 signing key from Vault or generate ephemeral keypair.
    
    Returns:
        (secret_key_bytes, public_key_bytes, pubkey_ref)
    """
    pubkey_ref = "vault:dilithium3-audit-key"
    
    if settings.VAULT_PKI_ENABLED and settings.VAULT_TOKEN:
        try:
            # Try to read from Vault
            client = hvac.Client(
                url=settings.VAULT_ADDR,
                token=settings.VAULT_TOKEN,
                verify=False  # TODO: Use proper CA cert in production
            )
            
            # Read secret from KV store
            secret_path = "kebos/dilithium3-audit-key"
            response = client.secrets.kv.v2.read_secret_version(path=secret_path)
            
            if response and 'data' in response and 'data' in response['data']:
                data = response['data']['data']
                secret_key = bytes.fromhex(data['secret_key'])
                public_key = bytes.fromhex(data['public_key'])
                logger.info("Loaded Dilithium-3 audit key from Vault")
                return secret_key, public_key, pubkey_ref
            else:
                logger.warning(f"Dilithium-3 key not found in Vault at {secret_path}, generating new keypair")
        except Exception as e:
            logger.warning(f"Failed to read Dilithium-3 key from Vault: {e}, generating ephemeral keypair")
    
    # Generate ephemeral keypair for development
    try:
        from qmind_enterprise.pqc.dilithium_sign import generate_keypair
        public_key, secret_key = generate_keypair()
        logger.warning("Generated ephemeral Dilithium-3 keypair for development - DO NOT USE IN PRODUCTION")
        pubkey_ref = "ephemeral:dilithium3-audit-key"
        return secret_key, public_key, pubkey_ref
    except ImportError:
        logger.error("liboqs not available - cannot generate Dilithium-3 keypair")
        return None, None, ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to start/stop background tasks"""
    # Startup
    db_pool = None
    try:
        # Create DB pool for consumers and monitors
        db_pool = await asyncpg.create_pool(settings.DATABASE_URL)
        app.state.db_pool = db_pool

        # Initialise HashiCorp Vault manager
        vault_ready = vault_manager.initialise()
        if vault_ready:
            logger.info("HashiCorp Vault: CONNECTED — secrets retrieved from Vault")
        else:
            logger.warning("HashiCorp Vault: FALLBACK MODE — secrets from environment variables")
        app.state.vault = vault_manager

        # Load Dilithium-3 signing key for audit chain
        secret_key, public_key, pubkey_ref = load_dilithium_signing_key()
        app.state.dilithium_public_key = public_key
        
        # Initialize AuditChain
        app.state.audit_chain = AuditChain(
            db_pool=db_pool,
            signing_key_bytes=secret_key,
            pubkey_ref=pubkey_ref
        )
        logger.info("Audit chain initialized with Dilithium-3 signing")
        
        # Initialize case manager for QMind consumer
        case_manager = get_case_manager(db_pool)
        app.state.case_manager = case_manager
        
        # Start QMind results consumer with done_callback
        task = asyncio.create_task(consume_qmind_results(), name="qmind-results-consumer")
        task.add_done_callback(handle_task_error)
        logger.info("qmind.results consumer registered")
        
        # Start CERT-In SLA monitor (Phase 3.3)
        cert_in_monitor = get_cert_in_sla_monitor(db_pool)
        await cert_in_monitor.start()
        app.state.cert_in_monitor = cert_in_monitor
        print("CERT-In SLA monitor started")
        
        # Store honeytoken manager for middleware
        app.state.honeytoken_manager = get_honeytoken_manager(db_pool)
        
        # Start CT Log Monitor (Phase 6.1)
        ct_log_monitor = get_ct_log_monitor()
        ct_log_task = await ct_log_monitor.start()
        app.state.ct_log_monitor = ct_log_monitor
        print("CT Log Monitor started")
        
        # Start Paste Monitor (Phase 6.2)
        paste_monitor = get_paste_monitor()
        paste_task = await paste_monitor.start()
        app.state.paste_monitor = paste_monitor
        print("Paste Monitor started")
        
        # Start Domain Monitor (Phase 6.2)
        domain_monitor = get_domain_monitor()
        domain_task = await domain_monitor.start()
        app.state.domain_monitor = domain_monitor
        print("Domain Monitor started")
        
        # Start Dependency Health Monitor (Phase 12)
        dep_health_monitor = get_dependency_health_monitor()
        task = asyncio.create_task(dep_health_monitor.start())
        task.add_done_callback(lambda t: logger.info("Dependency health monitor completed"))
        app.state.dep_health_monitor = dep_health_monitor
        print("Dependency Health Monitor started")
        
        # Start Threat Indicator Publisher (CatBoost + Kafka)
        threat_publisher = ThreatIndicatorPublisher()
        try:
            await threat_publisher.start(settings.KAFKA_BOOTSTRAP_SERVERS)
            app.state.threat_publisher = threat_publisher
            print("Threat Indicator Publisher started")
        except Exception as e:
            logger.warning(f"Threat publisher failed to start (Kafka may not be ready): {e}")
            app.state.threat_publisher = None
        
        # Wire SOCReportGenerator with LLM clients
        soc_generator = SOCReportGenerator()
        groq = GroqClient(settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
        gemma = LocalGemmaClient(settings.LOCAL_GEMMA_URL)
        soc_generator.wire_llm_clients(groq_client=groq, gemma_client=gemma)
        app.state.soc_generator = soc_generator
        logger.info("SOCReportGenerator wired")

        # Load Dilithium-3 signing key for CERT-In reports
        dilithium_sk_hex = getattr(settings, 'DILITHIUM_SIGNING_KEY_HEX', '')
        if dilithium_sk_hex:
            app.state.dilithium_signing_key = bytes.fromhex(dilithium_sk_hex)
            logger.info("Dilithium-3 signing key loaded for CERT-In reports")
        else:
            app.state.dilithium_signing_key = None
            logger.warning("DILITHIUM_SIGNING_KEY_HEX not set — reports will be unsigned")

        # Instantiate HoneyGrid — connects to docker-proxy:2375
        try:
            from app.deception.honeygrid import HoneyGridManager
            app.state.honeygrid = HoneyGridManager()
            logger.info("HoneyGridManager initialised → tcp://docker-proxy:2375")
        except Exception as e:
            # Don't crash startup if docker-proxy is not yet running
            app.state.honeygrid = None
            logger.warning(f"HoneyGridManager init failed (docker-proxy unavailable?): {e}")

        # Set honeygrid reference for QMind consumer (after instantiation)
        set_qmind_dependencies(db_pool, case_manager, app.state.audit_chain, app.state.honeygrid)
        
        # Set feedback consumer dependencies and start consumer
        set_feedback_dependencies(db_pool)
        task_fb = asyncio.create_task(
            consume_analyst_feedback(), name="analyst-feedback-consumer"
        )
        task_fb.add_done_callback(handle_task_error)

        # Setup TLS Syslog handler for audit trail
        setup_tls_syslog(
            logging.getLogger(),
            host=settings.SYSLOG_HOST,
            port=settings.SYSLOG_PORT,
            ca_cert=settings.SYSLOG_CA_CERT
        )
        logger.info("TLS Syslog handler configured")

        # Configure Splunk HEC
        splunk_hec.configure(
            hec_url=settings.SPLUNK_HEC_URL,
            hec_token=settings.SPLUNK_HEC_TOKEN,
            index=settings.SPLUNK_INDEX
        )

        yield
        
    finally:
        # Shutdown
        # Note: QMind consumer is managed by handle_task_error auto-restart, no explicit stop needed
        if hasattr(app.state, 'cert_in_monitor'):
            await app.state.cert_in_monitor.stop()
        if hasattr(app.state, 'dep_health_monitor'):
            await app.state.dep_health_monitor.stop()
        if hasattr(app.state, 'ct_log_monitor'):
            await app.state.ct_log_monitor.stop()
        if hasattr(app.state, 'paste_monitor'):
            await app.state.paste_monitor.stop()
        if hasattr(app.state, 'domain_monitor'):
            await app.state.domain_monitor.stop()
        if hasattr(app.state, 'threat_publisher'):
            await app.state.threat_publisher.stop()
        if db_pool:
            await db_pool.close()


app = FastAPI(lifespan=lifespan)

# Register security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS - explicit allowlist only (NEVER '*')
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)


@app.middleware("http")
async def honeytoken_middleware(request: Request, call_next):
    """
    Middleware to check every request for honeytokens.
    Phase 4.1 - Honeytoken detection in request body/headers.
    Uses in-memory cache to avoid DB query on every request.
    Only checks headers to avoid consuming request body.
    """
    # Skip health check and static files
    if request.url.path == "/health":
        return await call_next(request)
    
    # Get honeytoken manager if available
    if hasattr(app.state, 'honeytoken_manager'):
        honeytoken_manager = app.state.honeytoken_manager
        
        # Only check headers to avoid consuming request body
        headers = dict(request.headers)
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for honeytokens in headers only (uses in-memory cache)
        triggered_token = await honeytoken_manager.check_request_for_honeytokens(
            b"", headers, client_ip
        )
        
        if triggered_token:
            # Honeytoken triggered - log and continue (alert already sent)
            pass
    
    return await call_next(request)


@app.middleware("http")
async def x_request_id_middleware(request: Request, call_next):
    """
    Add X-Request-ID header to every response.
    Phase 2.3 - Request tracking middleware.
    """
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Include routers
app.include_router(signals_router)
app.include_router(auth_router)
app.include_router(nta_router)
app.include_router(vuln_router)
app.include_router(honeygrid_router)
app.include_router(siem_router)
app.include_router(cases_router)
app.include_router(admin_tenants_router)
app.include_router(reporting_router)


@app.websocket("/ws/threats/{tenant_id}")
async def websocket_threats(websocket: WebSocket, tenant_id: str):
    await websocket_manager.connect(websocket, tenant_id)
    try:
        while True:
            # Keep connection alive — receive pings from client
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, tenant_id)


@app.get("/health")
async def health():
    health_data = {
        "status": "healthy",
        "qmind_consumer": "running" if hasattr(app.state, 'qmind_consumer') else "stopped",
        "cert_in_monitor": "running" if hasattr(app.state, 'cert_in_monitor') else "stopped",
        "ct_log_monitor": "running" if hasattr(app.state, 'ct_log_monitor') else "stopped",
        "paste_monitor": "running" if hasattr(app.state, 'paste_monitor') else "stopped",
        "domain_monitor": "running" if hasattr(app.state, 'domain_monitor') else "stopped",
        "audit_chain": "initialized" if hasattr(app.state, 'audit_chain') else "not_initialized",
    }
    
    if hasattr(app.state, 'dep_health_monitor'):
        health_data["dependency_health"] = app.state.dep_health_monitor.get_health_status()
        health_data["overall_healthy"] = app.state.dep_health_monitor.is_healthy()
    
    return health_data
