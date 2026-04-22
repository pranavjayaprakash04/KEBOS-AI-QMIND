import json, asyncio
from app.integrations.egress_control import EgressControlledClient
from abc import ABC, abstractmethod
from app.config import settings

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
