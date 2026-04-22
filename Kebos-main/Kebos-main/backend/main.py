from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Import compatible modules for CTP
from auth.api import router as auth_router
from audit_logger.api import router as audit_logger_router
from job_manager.api import router as job_manager_router

# Import new CTP modules
from threat_detection.api import router as threat_detection_router
from genai_assistant.api import router as assistant_router  # Re-enabled with Gemma LLM
from siem_integration.api import router as siem_router
from network_analytics.api import router as network_router

# Import messaging module
from messaging.api import router as messaging_router
from messaging.websocket import websocket_router

# Import dashboard module
from dashboard.api import router as dashboard_router

app = FastAPI(
    title="Cyber Threat Platform (CTP) API",
    description="Real-time cyber threat prediction and mitigation platform with AI-powered analysis and secure messaging.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration - secure by default for zero-trust architecture
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register compatible routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(audit_logger_router, prefix="/audit", tags=["Security Audit"])
app.include_router(job_manager_router, prefix="/jobs", tags=["Job Management"])

# Register new CTP routers
app.include_router(threat_detection_router, prefix="/threats", tags=["Threat Detection"])
app.include_router(assistant_router, prefix="/assistant", tags=["GenAI Assistant"])  # Re-enabled with Gemma LLM
app.include_router(siem_router, prefix="/siem", tags=["SIEM Integration"])
app.include_router(network_router, prefix="/network", tags=["Network Analytics"])

# Register messaging routers
app.include_router(messaging_router, prefix="/messaging", tags=["Secure Messaging"])
app.include_router(websocket_router, prefix="/messaging", tags=["Real-time Messaging"])

# Register dashboard router
app.include_router(dashboard_router, tags=["Dashboard"])

@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint."""
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize CatBoost threat detector
        from threat_detection.catboost_detector import catboost_detector
        await catboost_detector.initialize()
        logger.info("CatBoost threat detector initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize CatBoost threat detector: {e}")
        # Continue startup even if CatBoost fails to initialize
