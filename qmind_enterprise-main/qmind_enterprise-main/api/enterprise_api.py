"""
Q-MIND Enterprise: FastAPI Routes

REST API for the enterprise threat intelligence platform.

Endpoints:
- POST /analyze: Analyze an indicator, get threat assessment
- POST /recommend: Get mitigation recommendations
- GET /status/{indicator}: Get current threat state
- POST /feedback: Record ground truth for accuracy evaluation
- GET /metrics: System accuracy metrics
- GET /health: API health check
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import logging
import uuid
import hashlib

# Import core components
from core.threat_state import (
    ThreatCategory, IndicatorSignature, ThreatState, ThreatStateManager
)
from signals.threat_signals import SignalWeightManager
from datasets.adapters import DatasetRegistry
from mitigation.recommendation_engine import MitigationEngine
from evaluation.accuracy_metrics import EvaluationFramework, GroundTruth

logger = logging.getLogger(__name__)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class IndicatorRequest(BaseModel):
    """Request to analyze an indicator."""
    indicator_type: str  # "url", "hash", "ip", "domain", "cve", etc.
    indicator_value: str
    category: str  # Threat category


class AnalysisResponse(BaseModel):
    """Response from threat analysis."""
    analysis_id: str
    indicator_type: str
    indicator_value: str
    category: str
    
    # Threat assessment
    threat_level: str  # critical, high, medium, low, minimal
    confidence: float  # [0, 1]
    malicious_probability: float
    suspicious_probability: float
    benign_probability: float
    
    # Lead time
    lead_time_hours: int
    
    # Metadata
    analyzed_at: str
    signals_used: List[str]


class RecommendationRequest(BaseModel):
    """Request for mitigation recommendations."""
    indicator_type: str
    indicator_value: str
    category: str


class MitigationActionResponse(BaseModel):
    """Single mitigation action."""
    action: str
    target: str
    priority: int
    confidence: float
    reasoning: str
    reversibility: str


class RecommendationResponse(BaseModel):
    """Response with mitigation recommendations."""
    plan_id: str
    primary_action: MitigationActionResponse
    secondary_actions: List[MitigationActionResponse]
    threat_level: str


class FeedbackRequest(BaseModel):
    """Ground truth feedback."""
    indicator_type: str
    indicator_value: str
    category: str
    ground_truth: str  # "malicious", "suspicious", "benign", "unknown"
    discovered_at: Optional[datetime] = None
    analyst_notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Feedback processing response."""
    status: str
    message: str


class MetricsResponse(BaseModel):
    """System accuracy metrics."""
    precision: float
    recall: float
    f1_score: float
    accuracy: float
    total_analyses: int
    per_category: Dict[str, Dict]


# ============================================================================
# API APPLICATION
# ============================================================================

class Q_MIND_Enterprise_API:
    """
    Enterprise threat intelligence API.
    
    Integrates all Q-MIND components: signal processing, threat state management,
    mitigation recommendations, and accuracy evaluation.
    """
    
    def __init__(self):
        self.app = FastAPI(
            title="Q-MIND Enterprise",
            description="Multi-category threat intelligence platform",
            version="1.0.0"
        )
        
        # Initialize core components
        self.threat_state_manager = ThreatStateManager()
        self.signal_weight_manager = SignalWeightManager()
        self.dataset_registry = DatasetRegistry()
        self.mitigation_engine = MitigationEngine()
        self.evaluation_framework = EvaluationFramework()
        
        # Setup API routes
        self._setup_routes()
        
        # API state
        self.api_token = self._generate_token()
        logger.info(f"Q-MIND Enterprise API initialized (token={self.api_token[:8]}...)")
    
    def _generate_token(self) -> str:
        """Generate API authentication token."""
        raw_token = f"{datetime.utcnow().isoformat()}-{uuid.uuid4()}"
        return hashlib.sha256(raw_token.encode()).hexdigest()[:32]
    
    def _verify_token(self, authorization: Optional[str]) -> bool:
        """Verify API token."""
        if not authorization:
            return False
        parts = authorization.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            return False
        return parts[1] == self.api_token
    
    def _setup_routes(self):
        """Setup all API routes."""
        
        @self.app.post("/analyze", response_model=AnalysisResponse)
        async def analyze(
            request: IndicatorRequest,
            authorization: Optional[str] = Header(None)
        ):
            """
            Analyze a threat indicator.
            
            Returns threat level, confidence, and signals used.
            """
            # Token verification
            if not self._verify_token(authorization):
                raise HTTPException(status_code=401, detail="Invalid or missing token")
            
            try:
                # Parse request
                category = ThreatCategory[request.category.upper()]
                
                # Get or create threat state
                indicator = IndicatorSignature(
                    indicator_type=request.indicator_type,
                    indicator_value=request.indicator_value,
                    category=category
                )
                
                threat_state = self.threat_state_manager.get_or_create_state(indicator)
                
                # Measure current state
                decision = threat_state.measure()
                
                # Record for evaluation
                analysis_id = str(uuid.uuid4())[:8]
                
                self.evaluation_framework.record_analysis(
                    indicator=indicator,
                    threat_state=threat_state,
                    predicted_threat_level=decision.get("threat_level", "minimal"),
                    predicted_confidence=decision.get("confidence", 0.5),
                    prediction_lead_time_hours=decision.get("lead_time_hours", 0)
                )
                
                # Build response
                amplitudes = threat_state.amplitudes
                
                return AnalysisResponse(
                    analysis_id=analysis_id,
                    indicator_type=request.indicator_type,
                    indicator_value=request.indicator_value,
                    category=request.category,
                    threat_level=decision.get("threat_level", "minimal"),
                    confidence=decision.get("confidence", 0.5),
                    malicious_probability=amplitudes.get("malicious", 0.0),
                    suspicious_probability=amplitudes.get("suspicious", 0.0),
                    benign_probability=amplitudes.get("benign", 0.0),
                    lead_time_hours=decision.get("lead_time_hours", 0),
                    analyzed_at=datetime.utcnow().isoformat(),
                    signals_used=list(threat_state.signals_used()) if hasattr(threat_state, 'signals_used') else []
                )
            
            except Exception as e:
                logger.error(f"Analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/recommend", response_model=RecommendationResponse)
        async def recommend(
            request: RecommendationRequest,
            authorization: Optional[str] = Header(None)
        ):
            """
            Get mitigation recommendations for a threat indicator.
            """
            if not self._verify_token(authorization):
                raise HTTPException(status_code=401, detail="Invalid or missing token")
            
            try:
                category = ThreatCategory[request.category.upper()]
                
                indicator = IndicatorSignature(
                    indicator_type=request.indicator_type,
                    indicator_value=request.indicator_value,
                    category=category
                )
                
                threat_state = self.threat_state_manager.get_or_create_state(indicator)
                
                # Generate recommendations
                plan = self.mitigation_engine.generate_recommendations(
                    indicator=indicator,
                    threat_state=threat_state
                )
                
                # Build response
                primary = plan.primary_recommendation
                
                return RecommendationResponse(
                    plan_id=plan.plan_id,
                    primary_action=MitigationActionResponse(
                        action=primary.action.value,
                        target=primary.target,
                        priority=primary.priority,
                        confidence=primary.confidence,
                        reasoning=primary.reasoning,
                        reversibility=primary.reversibility.value
                    ),
                    secondary_actions=[
                        MitigationActionResponse(
                            action=r.action.value,
                            target=r.target,
                            priority=r.priority,
                            confidence=r.confidence,
                            reasoning=r.reasoning,
                            reversibility=r.reversibility.value
                        )
                        for r in plan.secondary_recommendations
                    ],
                    threat_level=self._get_threat_level(threat_state)
                )
            
            except Exception as e:
                logger.error(f"Recommendation generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/feedback", response_model=FeedbackResponse)
        async def feedback(
            request: FeedbackRequest,
            authorization: Optional[str] = Header(None)
        ):
            """
            Submit ground truth feedback for accuracy evaluation.
            
            Enables learning loop: when actual outcome is known,
            update threat state with ground truth.
            """
            if not self._verify_token(authorization):
                raise HTTPException(status_code=401, detail="Invalid or missing token")
            
            try:
                category = ThreatCategory[request.category.upper()]
                
                indicator = IndicatorSignature(
                    indicator_type=request.indicator_type,
                    indicator_value=request.indicator_value,
                    category=category
                )
                
                threat_state = self.threat_state_manager.get_or_create_state(indicator)
                
                # Record ground truth
                ground_truth = GroundTruth[request.ground_truth.upper()]
                
                threat_state.record_ground_truth(
                    actual_threat=(ground_truth == GroundTruth.MALICIOUS),
                    actual_category=category,
                    timing="timely" if not request.discovered_at else "early"
                )
                
                return FeedbackResponse(
                    status="accepted",
                    message=f"Ground truth recorded for {request.indicator_value}"
                )
            
            except Exception as e:
                logger.error(f"Feedback processing failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics", response_model=MetricsResponse)
        async def metrics(
            authorization: Optional[str] = Header(None)
        ):
            """
            Get system accuracy metrics.
            """
            if not self._verify_token(authorization):
                raise HTTPException(status_code=401, detail="Invalid or missing token")
            
            try:
                agg = self.evaluation_framework.get_aggregate_metrics()
                
                return MetricsResponse(
                    precision=agg.precision(),
                    recall=agg.recall(),
                    f1_score=agg.f1_score(),
                    accuracy=agg.accuracy(),
                    total_analyses=self.evaluation_framework.record_count,
                    per_category={
                        cat.value: self.evaluation_framework.category_metrics[cat].export()
                        for cat in ThreatCategory
                    }
                )
            
            except Exception as e:
                logger.error(f"Metrics retrieval failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health")
        async def health():
            """API health check."""
            return {
                "status": "healthy",
                "components": {
                    "threat_state_manager": "ok",
                    "mitigation_engine": "ok",
                    "evaluation_framework": "ok",
                    "dataset_registry": "ok"
                },
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _get_threat_level(self, threat_state: ThreatState) -> str:
        """Get threat level from state."""
        decision = threat_state.measure()
        return decision.get("threat_level", "minimal")
    
    def get_app(self) -> FastAPI:
        """Get FastAPI application."""
        return self.app


# ============================================================================
# API INITIALIZATION
# ============================================================================

def create_api() -> FastAPI:
    """Factory function to create and configure API."""
    api = Q_MIND_Enterprise_API()
    return api.get_app()


# Run with: uvicorn --reload
if __name__ == "__main__":
    import uvicorn
    app = create_api()
    uvicorn.run(app, host="0.0.0.0", port=8000)
