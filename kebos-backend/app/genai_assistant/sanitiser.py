"""
LLM Data Sanitiser for Kebos AI.
Security control — runs before EVERY external LLM call.
Ensures customer PII and tenant data never reaches external APIs.
DPDPA compliance: CONFIDENTIAL/RESTRICTED data stays in India (local Gemma).
"""


class LLMDataSanitiser:
    """
    Security control — runs before EVERY external LLM call.
    Ensures customer PII and tenant data never reaches external APIs.
    DPDPA compliance: CONFIDENTIAL/RESTRICTED data stays in India (local Gemma).
    """
    SAFE_FOR_EXTERNAL = {
        "lead_category", "confidence", "category_scores", "reversibility",
        "advisory", "indicator_type", "threat_level", "recommended_actions",
        "mitre_techniques", "source",
    }
    NEVER_EXTERNAL = {
        "source_ip", "internal_hostname", "username", "customer_id",
        "asset_inventory", "raw_logs", "tenant_id", "employee_id",
        "account_number", "aadhaar", "pan_card", "upi_id", "ifsc_code",
    }

    def sanitise(self, payload: dict, classification: str) -> dict:
        if classification in ("CONFIDENTIAL", "RESTRICTED"):
            raise ValueError(
                f"Data classified {classification} must use local Gemma — "
                "NEVER send to external LLM (DPDPA violation)"
            )
        sanitised = {k: v for k, v in payload.items()
                     if k in self.SAFE_FOR_EXTERNAL}
        # Hard check: NEVER_EXTERNAL fields must never be in sanitised output
        leaked = self.NEVER_EXTERNAL.intersection(sanitised.keys())
        if leaked:
            raise AssertionError(
                f"Security: {leaked} would leak to external LLM. "
                "Check SAFE_FOR_EXTERNAL set."
            )
        return sanitised
