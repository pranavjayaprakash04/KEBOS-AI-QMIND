import json, asyncio
from app.integrations.egress_control import EgressControlledClient
from abc import ABC, abstractmethod
from app.config import settings

HONEYPOT_BRIEF_PROMPT = """
You are a threat intelligence analyst reviewing an attacker session
captured by a cyber deception honeypot system.

Attacker IP: {attacker_ip}
Trap engaged: {trap_type}
Threat category: {category}
Adversarial stability score: {stability_score:.2f} / 1.00
Feed sources that flagged this IP: {feed_sources}
Interaction summary: {interaction_summary}

Write exactly 4 sentences:
1. Attacker likely profile and origin based on IP intelligence and behaviour
2. What they were attempting to do (specific tactic observed)
3. Known threat actor group association if any (state Unknown if none)
4. Immediate recommended action for the SOC analyst

Rules: Be direct. No hedging language. Maximum 100 words total.
"""

class LLMClient(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str) -> str: ...

class GroqClient(LLMClient):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        self.api_key = api_key
        self.model = model

    async def complete(self, system: str, user: str) -> str:
        async with EgressControlledClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model,
                      "messages": [{"role": "system", "content": system},
                                   {"role": "user", "content": user}],
                      "response_format": {"type": "json_object"}}
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

class LocalGemmaClient(LLMClient):
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url

    async def complete(self, system: str, user: str) -> str:
        async with EgressControlledClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": "gemma:2b",
                      "prompt": f"System: {system}\n\nUser: {user}",
                      "format": "json", "stream": False}
            )
            resp.raise_for_status()
            return resp.json()["response"]

class LLMRouter:
    def get_client(self, classification: str, tenant_type: str) -> LLMClient:
        # Government tenants ALWAYS use local Gemma — no exceptions
        if tenant_type == "government":
            return LocalGemmaClient(settings.LOCAL_GEMMA_URL)
        if classification in ("CONFIDENTIAL", "RESTRICTED"):
            return LocalGemmaClient(settings.LOCAL_GEMMA_URL)
        if classification in ("PUBLIC", "INTERNAL"):
            if settings.GROQ_API_KEY:
                return GroqClient(settings.GROQ_API_KEY)
            return LocalGemmaClient(settings.LOCAL_GEMMA_URL)
        raise ValueError(f"Unknown classification: {classification}")


async def generate_honeypot_brief(context: dict) -> str:
    """
    Generate a honeypot brief using the HONEYPOT_BRIEF_PROMPT.

    Args:
        context: Dict with keys: attacker_ip, trap_type, category, stability_score,
               feed_sources, interaction_summary

    Returns:
        Brief string or fallback message on LLM failure
    """
    attacker_ip = context.get("attacker_ip", "unknown")

    try:
        # Format the prompt with context
        prompt = HONEYPOT_BRIEF_PROMPT.format(
            attacker_ip=attacker_ip,
            trap_type=context.get("trap_type", "unknown"),
            category=context.get("category", "Unknown"),
            stability_score=context.get("stability_score", 0.0),
            feed_sources=context.get("feed_sources", "none"),
            interaction_summary=context.get("interaction_summary", "")
        )

        # Use LocalGemmaClient for brief generation
        client = LocalGemmaClient(settings.LOCAL_GEMMA_URL)
        brief = await client.complete(
            system="You are a threat intelligence analyst.",
            user=prompt
        )

        return brief

    except Exception as e:
        logging.getLogger(__name__).error(f"LLM brief generation failed for {attacker_ip}: {e}")
        return f"Automated brief generation failed. Manual analyst review required for IP: {attacker_ip}"
