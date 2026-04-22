#!/usr/bin/env python3
"""
Simple test script to verify CatBoost integration works without all the other dependencies.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Create a simple FastAPI app with just CatBoost
app = FastAPI(
    title="CatBoost Test API",
    description="Simple test for CatBoost threat detection",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import only the threat detection module
from threat_detection.api import router as threat_detection_router

# Register only the threat detection router
app.include_router(threat_detection_router, prefix="/threat", tags=["Threat Detection"])

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "message": "CatBoost test API is running"}

@app.on_event("startup")
async def startup_event():
    """Initialize CatBoost threat detector on startup."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    try:
        from threat_detection.catboost_detector import catboost_detector
        await catboost_detector.initialize()
        logger.info("CatBoost threat detector initialized successfully!")
        
        # Test the detector health
        health_status = await catboost_detector.get_health_status()
        logger.info(f"CatBoost health status: {health_status}")
        
    except Exception as e:
        logger.error(f"Failed to initialize CatBoost threat detector: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
