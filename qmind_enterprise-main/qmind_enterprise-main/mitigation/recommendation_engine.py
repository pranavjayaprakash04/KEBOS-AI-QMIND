"""
Q-MIND Enterprise: Mitigation Recommendation Engine

Converts threat signals and state measurements to actionable recommendations.

Philosophy:
- Advisory-first: Recommendations are suggestions, never auto-enforced
- Explainable: Every recommendation includes reasoning
- Reversible-aware: Clear distinction between reversible/non-reversible actions
- Confidence-driven: Recommendations weighted by decision confidence
- Risk-based: Lead-time tailored to threat level and decision urgency
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional
from datetime import timedelta
import logging

from core.threat_state import ThreatCategory, IndicatorSignature, ThreatState

logger = logging.getLogger(__name__)


class MitigationAction(str, Enum):
    """Available mitigation actions across all threat types."""
    
    # Blocking/Filtering
    BLOCK_DOMAIN = "block_domain"
    BLOCK_IP = "block_ip"
    BLOCK_URL = "block_url"
    BLOCK_HASH = "block_hash"
    
    # Isolation
    ISOLATE_HOST = "isolate_host"
    DISCONNECT_USER = "disconnect_user"
    REVOKE_CREDENTIALS = "revoke_credentials"
    
    # Alerting
    ESCALATE_TO_SOC = "escalate_to_soc"
    NOTIFY_SECURITY_TEAM = "notify_security_team"
    CREATE_INCIDENT = "create_incident"
    
    # Patching
    PATCH_SYSTEM = "patch_system"
    UPDATE_DEPENDENCY = "update_dependency"
    DISABLE_SERVICE = "disable_service"
    
    # Investigation
    DEEP_INSPECTION = "deep_inspection"
    BEHAVIORAL_MONITORING = "behavioral_monitoring"
    NETWORK_CAPTURE = "network_capture"
    
    # Remediation
    WAF_RULE = "waf_rule"
    HONEY_TRAP = "honey_trap"
    SINKHOLE = "sinkhole"


class ActionReversibility(str, Enum):
    """Action reversibility classification."""
    FULLY_REVERSIBLE = "fully_reversible"  # Can be undone immediately
    REVERSIBLE_WITH_EFFORT = "reversible_with_effort"  # Can be undone but requires time
    NON_REVERSIBLE = "non_reversible"  # Cannot be undone


@dataclass
class MitigationRecommendation:
    """Single mitigation recommendation."""
    
    action: MitigationAction
    target: str  # What to act on (IP, domain, hash, user_id, etc.)
    category: ThreatCategory
    
    # Recommendation quality
    priority: int  # 1=critical, 2=high, 3=medium, 4=low
    confidence: float  # [0, 1] - how confident is this recommendation?
    lead_time_hours: int  # How long before threat materializes
    
    # Rationale
    reasoning: str  # Why this recommendation
    signals_contributing: List[str] = field(default_factory=list)
    
    # Implementation guidance
    reversibility: ActionReversibility = ActionReversibility.FULLY_REVERSIBLE
    estimated_effort_minutes: int = 0  # Time to implement
    prerequisites: List[str] = field(default_factory=list)  # What must be done first
    
    # Tracking
    timestamp: float = 0.0
    recommendation_id: str = ""
    
    def export(self) -> Dict:
        """Export to JSON-serializable format."""
        return {
            "recommendation_id": self.recommendation_id,
            "action": self.action.value,
            "target": self.target,
            "category": self.category.value,
            "priority": self.priority,
            "confidence": self.confidence,
            "lead_time_hours": self.lead_time_hours,
            "reasoning": self.reasoning,
            "reversibility": self.reversibility.value,
            "estimated_effort_minutes": self.estimated_effort_minutes,
        }


@dataclass
class MitigationPlan:
    """Complete mitigation plan for a threat indicator."""
    
    indicator: IndicatorSignature
    threat_state: ThreatState
    
    primary_recommendation: MitigationRecommendation
    secondary_recommendations: List[MitigationRecommendation] = field(default_factory=list)
    
    # Plan metadata
    created_at: float = 0.0
    plan_id: str = ""
    accepted: bool = False
    implemented_actions: List[str] = field(default_factory=list)  # What was actually done
    
    def export(self) -> Dict:
        """Export to JSON-serializable format."""
        return {
            "plan_id": self.plan_id,
            "indicator_type": self.indicator.indicator_type,
            "indicator_value": self.indicator.indicator_value,
            "threat_level": self._get_threat_level(),
            "primary_action": self.primary_recommendation.export(),
            "secondary_actions": [r.export() for r in self.secondary_recommendations],
            "implemented": self.implemented_actions,
        }
    
    def _get_threat_level(self) -> str:
        """Get human-readable threat level."""
        decision = self.threat_state.measure()
        level = decision.get("threat_level", "minimal")
        return level


# ============================================================================
# MITIGATION RECOMMENDATION ENGINE
# ============================================================================

class MitigationEngine:
    """
    Core recommendation engine that generates mitigation plans.
    
    For each threat indicator, produces prioritized recommendations
    based on threat category, confidence, and lead time.
    """
    
    # Threat-level to action mapping
    THREAT_LEVEL_ACTIONS = {
        "critical": [
            MitigationAction.ESCALATE_TO_SOC,
            MitigationAction.CREATE_INCIDENT,
        ],
        "high": [
            MitigationAction.NOTIFY_SECURITY_TEAM,
            MitigationAction.DEEP_INSPECTION,
        ],
        "medium": [
            MitigationAction.BEHAVIORAL_MONITORING,
        ],
        "low": [
            MitigationAction.NETWORK_CAPTURE,
        ],
        "minimal": [],
    }
    
    def __init__(self):
        self.recommendation_count = 0
        self.plan_cache = {}  # indicator → plan
    
    def generate_recommendations(
        self,
        indicator: IndicatorSignature,
        threat_state: ThreatState,
    ) -> MitigationPlan:
        """
        Generate mitigation plan for a threat indicator.
        
        Returns: MitigationPlan with primary + secondary recommendations
        """
        
        # Measure current threat state
        decision = threat_state.measure()
        threat_level = decision.get("threat_level", "minimal")
        confidence = decision.get("confidence", 0.5)
        lead_time = decision.get("lead_time_hours", 0)
        
        # Generate recommendations based on threat type
        if indicator.category == ThreatCategory.PHISHING:
            plan = self._recommend_phishing(
                indicator, threat_state, threat_level, confidence, lead_time
            )
        elif indicator.category == ThreatCategory.MALWARE:
            plan = self._recommend_malware(
                indicator, threat_state, threat_level, confidence, lead_time
            )
        elif indicator.category == ThreatCategory.C2_INFRASTRUCTURE:
            plan = self._recommend_c2(
                indicator, threat_state, threat_level, confidence, lead_time
            )
        elif indicator.category == ThreatCategory.BOTNET_IP:
            plan = self._recommend_botnet(
                indicator, threat_state, threat_level, confidence, lead_time
            )
        elif indicator.category == ThreatCategory.CREDENTIAL_LEAK:
            plan = self._recommend_credential(
                indicator, threat_state, threat_level, confidence, lead_time
            )
        elif indicator.category == ThreatCategory.VULNERABILITY:
            plan = self._recommend_vulnerability(
                indicator, threat_state, threat_level, confidence, lead_time
            )
        elif indicator.category == ThreatCategory.INSIDER_THREAT:
            plan = self._recommend_insider_threat(
                indicator, threat_state, threat_level, confidence, lead_time
            )
        elif indicator.category == ThreatCategory.SUPPLY_CHAIN:
            plan = self._recommend_supply_chain(
                indicator, threat_state, threat_level, confidence, lead_time
            )
        elif indicator.category == ThreatCategory.DDOS:
            plan = self._recommend_ddos(
                indicator, threat_state, threat_level, confidence, lead_time
            )
        else:
            # Benign/unknown
            primary = MitigationRecommendation(
                action=MitigationAction.BEHAVIORAL_MONITORING,
                target=indicator.indicator_value,
                category=indicator.category,
                priority=4,
                confidence=0.5,
                lead_time_hours=0,
                reasoning="Unknown indicator type - monitor for unusual activity",
            )
            plan = MitigationPlan(
                indicator=indicator,
                threat_state=threat_state,
                primary_recommendation=primary,
            )
        
        # Cache and return
        self.recommendation_count += 1
        plan.plan_id = f"PLAN-{self.recommendation_count:08d}"
        self.plan_cache[str(indicator)] = plan
        
        return plan
    
    # ====== Category-specific recommendation generators ======
    
    def _recommend_phishing(
        self, indicator, threat_state, threat_level, confidence, lead_time
    ) -> MitigationPlan:
        """Recommendations for phishing threats."""
        
        priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(threat_level, 4)
        
        primary = MitigationRecommendation(
            action=MitigationAction.BLOCK_URL,
            target=indicator.indicator_value,
            category=ThreatCategory.PHISHING,
            priority=priority,
            confidence=confidence,
            lead_time_hours=lead_time,
            reasoning=f"Phishing URL with {threat_level} threat level detected. "
                     f"Block at WAF/DNS to prevent user access.",
            signals_contributing=["lexical_analysis", "reputation_database"],
            reversibility=ActionReversibility.FULLY_REVERSIBLE,
            estimated_effort_minutes=2,
            prerequisites=["WAF access"],
        )
        
        secondary = [
            MitigationRecommendation(
                action=MitigationAction.ESCALATE_TO_SOC,
                target=indicator.indicator_value,
                category=ThreatCategory.PHISHING,
                priority=2,
                confidence=confidence,
                lead_time_hours=lead_time,
                reasoning="Notify SOC for phishing investigation and user awareness training",
                reversibility=ActionReversibility.FULLY_REVERSIBLE,
                estimated_effort_minutes=5,
            ),
            MitigationRecommendation(
                action=MitigationAction.NETWORK_CAPTURE,
                target=indicator.indicator_value,
                category=ThreatCategory.PHISHING,
                priority=3,
                confidence=confidence,
                lead_time_hours=lead_time,
                reasoning="Capture network traffic for phishing infrastructure analysis",
                reversibility=ActionReversibility.FULLY_REVERSIBLE,
                estimated_effort_minutes=10,
            )
        ]
        
        return MitigationPlan(
            indicator=indicator,
            threat_state=threat_state,
            primary_recommendation=primary,
            secondary_recommendations=secondary,
        )
    
    def _recommend_malware(
        self, indicator, threat_state, threat_level, confidence, lead_time
    ) -> MitigationPlan:
        """Recommendations for malware threats."""
        
        priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(threat_level, 4)
        
        primary = MitigationRecommendation(
            action=MitigationAction.BLOCK_HASH,
            target=indicator.indicator_value,
            category=ThreatCategory.MALWARE,
            priority=priority,
            confidence=confidence,
            lead_time_hours=lead_time,
            reasoning=f"Malware hash with {threat_level} threat. Block on all endpoints "
                     f"and add to EDR exclusion list.",
            signals_contributing=["virustotal", "malware_taxonomy"],
            reversibility=ActionReversibility.FULLY_REVERSIBLE,
            estimated_effort_minutes=15,
            prerequisites=["EDR console access"],
        )
        
        secondary = [
            MitigationRecommendation(
                action=MitigationAction.DEEP_INSPECTION,
                target=indicator.indicator_value,
                category=ThreatCategory.MALWARE,
                priority=2,
                confidence=confidence,
                lead_time_hours=lead_time,
                reasoning="Sandboxed detonation and behavior analysis",
                reversibility=ActionReversibility.FULLY_REVERSIBLE,
                estimated_effort_minutes=30,
                prerequisites=["Sandbox access"],
            ),
        ]
        
        return MitigationPlan(
            indicator=indicator,
            threat_state=threat_state,
            primary_recommendation=primary,
            secondary_recommendations=secondary,
        )
    
    def _recommend_c2(
        self, indicator, threat_state, threat_level, confidence, lead_time
    ) -> MitigationPlan:
        """Recommendations for C2 infrastructure."""
        
        priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(threat_level, 4)
        
        primary = MitigationRecommendation(
            action=MitigationAction.BLOCK_IP,
            target=indicator.indicator_value,
            category=ThreatCategory.C2_INFRASTRUCTURE,
            priority=priority,
            confidence=confidence,
            lead_time_hours=lead_time,
            reasoning=f"Known C2 infrastructure with {threat_level} threat. "
                     f"Block egress traffic immediately.",
            signals_contributing=["network_behavior", "feodo_tracker"],
            reversibility=ActionReversibility.FULLY_REVERSIBLE,
            estimated_effort_minutes=5,
            prerequisites=["Firewall admin"],
        )
        
        secondary = [
            MitigationRecommendation(
                action=MitigationAction.SINKHOLE,
                target=indicator.indicator_value,
                category=ThreatCategory.C2_INFRASTRUCTURE,
                priority=2,
                confidence=confidence,
                lead_time_hours=lead_time,
                reasoning="Redirect C2 traffic to sinkhole for forensics",
                reversibility=ActionReversibility.REVERSIBLE_WITH_EFFORT,
                estimated_effort_minutes=45,
                prerequisites=["DNS sinkhole setup"],
            ),
        ]
        
        return MitigationPlan(
            indicator=indicator,
            threat_state=threat_state,
            primary_recommendation=primary,
            secondary_recommendations=secondary,
        )
    
    def _recommend_botnet(
        self, indicator, threat_state, threat_level, confidence, lead_time
    ) -> MitigationPlan:
        """Recommendations for botnet IPs."""
        
        priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(threat_level, 4)
        
        primary = MitigationRecommendation(
            action=MitigationAction.BLOCK_IP,
            target=indicator.indicator_value,
            category=ThreatCategory.BOTNET_IP,
            priority=priority,
            confidence=confidence,
            lead_time_hours=lead_time,
            reasoning=f"Botnet IP with {threat_level} threat. Prevent inbound connections.",
            signals_contributing=["asn_reputation", "abuse_reports"],
            reversibility=ActionReversibility.FULLY_REVERSIBLE,
            estimated_effort_minutes=3,
        )
        
        secondary = []
        
        return MitigationPlan(
            indicator=indicator,
            threat_state=threat_state,
            primary_recommendation=primary,
            secondary_recommendations=secondary,
        )
    
    def _recommend_credential(
        self, indicator, threat_state, threat_level, confidence, lead_time
    ) -> MitigationPlan:
        """Recommendations for credential leaks."""
        
        priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(threat_level, 4)
        
        primary = MitigationRecommendation(
            action=MitigationAction.REVOKE_CREDENTIALS,
            target=indicator.indicator_value,
            category=ThreatCategory.CREDENTIAL_LEAK,
            priority=priority,
            confidence=confidence,
            lead_time_hours=lead_time,
            reasoning=f"Credentials found in breach with {threat_level} risk. "
                     f"Reset password and enable MFA.",
            signals_contributing=["breach_database"],
            reversibility=ActionReversibility.REVERSIBLE_WITH_EFFORT,
            estimated_effort_minutes=10,
            prerequisites=["Identity management access"],
        )
        
        secondary = []
        
        return MitigationPlan(
            indicator=indicator,
            threat_state=threat_state,
            primary_recommendation=primary,
            secondary_recommendations=secondary,
        )
    
    def _recommend_vulnerability(
        self, indicator, threat_state, threat_level, confidence, lead_time
    ) -> MitigationPlan:
        """Recommendations for vulnerability exploitation."""
        
        priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(threat_level, 4)
        
        primary = MitigationRecommendation(
            action=MitigationAction.PATCH_SYSTEM,
            target=indicator.indicator_value,
            category=ThreatCategory.VULNERABILITY,
            priority=priority,
            confidence=confidence,
            lead_time_hours=lead_time,
            reasoning=f"CVE with {threat_level} severity detected. "
                     f"Prioritize patching of affected systems.",
            signals_contributing=["nvd", "exploit_availability"],
            reversibility=ActionReversibility.REVERSIBLE_WITH_EFFORT,
            estimated_effort_minutes=120,  # Patching takes time
            prerequisites=["Patch management system", "Test environment"],
        )
        
        secondary = [
            MitigationRecommendation(
                action=MitigationAction.WAF_RULE,
                target=indicator.indicator_value,
                category=ThreatCategory.VULNERABILITY,
                priority=2,
                confidence=confidence,
                lead_time_hours=lead_time,
                reasoning="Deploy WAF rule as temporary protection until patching",
                reversibility=ActionReversibility.FULLY_REVERSIBLE,
                estimated_effort_minutes=20,
            ),
        ]
        
        return MitigationPlan(
            indicator=indicator,
            threat_state=threat_state,
            primary_recommendation=primary,
            secondary_recommendations=secondary,
        )
    
    def _recommend_insider_threat(
        self, indicator, threat_state, threat_level, confidence, lead_time
    ) -> MitigationPlan:
        """Recommendations for insider threats."""
        
        priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(threat_level, 4)
        
        primary = MitigationRecommendation(
            action=MitigationAction.ESCALATE_TO_SOC,
            target=indicator.indicator_value,
            category=ThreatCategory.INSIDER_THREAT,
            priority=priority,
            confidence=confidence,
            lead_time_hours=lead_time,
            reasoning=f"Behavioral anomaly with {threat_level} risk detected. "
                     f"Escalate to investigation team for manual review.",
            signals_contributing=["behavioral_anomaly", "ueba"],
            reversibility=ActionReversibility.FULLY_REVERSIBLE,
            estimated_effort_minutes=5,
        )
        
        secondary = [
            MitigationRecommendation(
                action=MitigationAction.BEHAVIORAL_MONITORING,
                target=indicator.indicator_value,
                category=ThreatCategory.INSIDER_THREAT,
                priority=2,
                confidence=confidence,
                lead_time_hours=lead_time,
                reasoning="Enable enhanced monitoring for this user",
                reversibility=ActionReversibility.FULLY_REVERSIBLE,
                estimated_effort_minutes=15,
            ),
        ]
        
        return MitigationPlan(
            indicator=indicator,
            threat_state=threat_state,
            primary_recommendation=primary,
            secondary_recommendations=secondary,
        )
    
    def _recommend_supply_chain(
        self, indicator, threat_state, threat_level, confidence, lead_time
    ) -> MitigationPlan:
        """Recommendations for supply chain attacks."""
        
        priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(threat_level, 4)
        
        primary = MitigationRecommendation(
            action=MitigationAction.UPDATE_DEPENDENCY,
            target=indicator.indicator_value,
            category=ThreatCategory.SUPPLY_CHAIN,
            priority=priority,
            confidence=confidence,
            lead_time_hours=lead_time,
            reasoning=f"Vulnerable dependency with {threat_level} risk. "
                     f"Update to patched version immediately.",
            signals_contributing=["dependency_scan"],
            reversibility=ActionReversibility.REVERSIBLE_WITH_EFFORT,
            estimated_effort_minutes=180,  # Testing required
            prerequisites=["CI/CD pipeline", "Test suite"],
        )
        
        secondary = []
        
        return MitigationPlan(
            indicator=indicator,
            threat_state=threat_state,
            primary_recommendation=primary,
            secondary_recommendations=secondary,
        )
    
    def _recommend_ddos(
        self, indicator, threat_state, threat_level, confidence, lead_time
    ) -> MitigationPlan:
        """Recommendations for DDoS threats."""
        
        priority = {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(threat_level, 4)
        
        primary = MitigationRecommendation(
            action=MitigationAction.ESCALATE_TO_SOC,
            target=indicator.indicator_value,
            category=ThreatCategory.DDOS,
            priority=priority,
            confidence=confidence,
            lead_time_hours=lead_time,
            reasoning=f"DDoS attack pattern with {threat_level} intensity detected. "
                     f"Activate DDoS mitigation service.",
            signals_contributing=["burst_detection", "traffic_analysis"],
            reversibility=ActionReversibility.FULLY_REVERSIBLE,
            estimated_effort_minutes=2,
        )
        
        secondary = []
        
        return MitigationPlan(
            indicator=indicator,
            threat_state=threat_state,
            primary_recommendation=primary,
            secondary_recommendations=secondary,
        )


logger.info("Q-MIND Enterprise: Mitigation engine initialized")
