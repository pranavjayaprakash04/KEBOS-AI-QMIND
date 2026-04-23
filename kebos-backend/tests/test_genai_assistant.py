"""
Tests for GenAI Assistant components.
Phase 2.2 - LLM Data Sanitiser and LLM Router.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.genai_assistant.sanitiser import LLMDataSanitiser
from app.genai_assistant.llm_router import LLMRouter, GroqClient, LocalGemmaClient


class TestLLMDataSanitiser:
    """Test suite for LLMDataSanitiser"""

    def test_sanitiser_strips_source_ip_from_payload(self):
        """Test that LLMDataSanitiser strips source_ip from payload"""
        sanitiser = LLMDataSanitiser()
        payload = {
            "source_ip": "192.168.1.1",
            "lead_category": "malware",
            "confidence": 0.95,
            "threat_level": "high",
        }
        result = sanitiser.sanitise(payload, "PUBLIC")
        assert "source_ip" not in result
        assert "lead_category" in result
        assert "confidence" in result
        assert "threat_level" in result

    def test_sanitiser_raises_value_error_for_confidential_classification(self):
        """Test that LLMDataSanitiser raises ValueError for CONFIDENTIAL classification"""
        sanitiser = LLMDataSanitiser()
        payload = {"lead_category": "malware", "confidence": 0.95}
        with pytest.raises(ValueError) as exc_info:
            sanitiser.sanitise(payload, "CONFIDENTIAL")
        assert "must use local Gemma" in str(exc_info.value)
        assert "DPDPA violation" in str(exc_info.value)

    def test_sanitiser_raises_value_error_for_restricted_classification(self):
        """Test that LLMDataSanitiser raises ValueError for RESTRICTED classification"""
        sanitiser = LLMDataSanitiser()
        payload = {"lead_category": "malware", "confidence": 0.95}
        with pytest.raises(ValueError) as exc_info:
            sanitiser.sanitise(payload, "RESTRICTED")
        assert "must use local Gemma" in str(exc_info.value)
        assert "DPDPA violation" in str(exc_info.value)

    def test_sanitiser_raises_assertion_error_if_never_external_field_leaks(self):
        """Test that LLMDataSanitiser raises AssertionError if NEVER_EXTERNAL field leaks"""
        sanitiser = LLMDataSanitiser()
        # Simulate a bug where source_ip is in SAFE_FOR_EXTERNAL (security check)
        payload = {
            "source_ip": "192.168.1.1",
            "lead_category": "malware",
        }
        # If source_ip somehow gets through, it should be caught
        with patch.object(sanitiser, 'SAFE_FOR_EXTERNAL', {"source_ip", "lead_category"}):
            with pytest.raises(AssertionError) as exc_info:
                sanitiser.sanitise(payload, "PUBLIC")
            assert "would leak to external LLM" in str(exc_info.value)

    def test_sanitiser_only_includes_safe_fields(self):
        """Test that sanitiser only includes fields from SAFE_FOR_EXTERNAL"""
        sanitiser = LLMDataSanitiser()
        payload = {
            "lead_category": "malware",
            "confidence": 0.95,
            "advisory": "Block immediately",
            "source": "threat_feed",
            "unknown_field": "should_be_removed",
        }
        result = sanitiser.sanitise(payload, "PUBLIC")
        assert "lead_category" in result
        assert "confidence" in result
        assert "advisory" in result
        assert "source" in result
        assert "unknown_field" not in result

    def test_sanitiser_handles_empty_payload(self):
        """Test that sanitiser handles empty payload"""
        sanitiser = LLMDataSanitiser()
        payload = {}
        result = sanitiser.sanitise(payload, "PUBLIC")
        assert result == {}


class TestLLMRouter:
    """Test suite for LLMRouter"""

    @patch('app.genai_assistant.llm_router.settings')
    def test_router_returns_local_gemma_for_government_tenants(self, mock_settings):
        """Test that LLMRouter returns LocalGemmaClient for government tenants"""
        mock_settings.LOCAL_GEMMA_URL = "http://localhost:11434"
        router = LLMRouter()
        client = router.get_client("PUBLIC", "government")
        assert isinstance(client, LocalGemmaClient)
        assert client.base_url == "http://localhost:11434"

    @patch('app.genai_assistant.llm_router.settings')
    def test_router_returns_local_gemma_for_confidential_data(self, mock_settings):
        """Test that LLMRouter returns LocalGemmaClient for CONFIDENTIAL data"""
        mock_settings.LOCAL_GEMMA_URL = "http://localhost:11434"
        router = LLMRouter()
        client = router.get_client("CONFIDENTIAL", "enterprise")
        assert isinstance(client, LocalGemmaClient)
        assert client.base_url == "http://localhost:11434"

    @patch('app.genai_assistant.llm_router.settings')
    def test_router_returns_local_gemma_for_restricted_data(self, mock_settings):
        """Test that LLMRouter returns LocalGemmaClient for RESTRICTED data"""
        mock_settings.LOCAL_GEMMA_URL = "http://localhost:11434"
        router = LLMRouter()
        client = router.get_client("RESTRICTED", "enterprise")
        assert isinstance(client, LocalGemmaClient)
        assert client.base_url == "http://localhost:11434"

    @patch('app.genai_assistant.llm_router.settings')
    def test_router_returns_groq_for_public_data_when_api_key_set(self, mock_settings):
        """Test that LLMRouter returns GroqClient for PUBLIC data when GROQ_API_KEY set"""
        mock_settings.GROQ_API_KEY = "test-api-key"
        mock_settings.LOCAL_GEMMA_URL = "http://localhost:11434"
        router = LLMRouter()
        client = router.get_client("PUBLIC", "enterprise")
        assert isinstance(client, GroqClient)
        assert client.api_key == "test-api-key"

    @patch('app.genai_assistant.llm_router.settings')
    def test_router_returns_groq_for_internal_data_when_api_key_set(self, mock_settings):
        """Test that LLMRouter returns GroqClient for INTERNAL data when GROQ_API_KEY set"""
        mock_settings.GROQ_API_KEY = "test-api-key"
        mock_settings.LOCAL_GEMMA_URL = "http://localhost:11434"
        router = LLMRouter()
        client = router.get_client("INTERNAL", "enterprise")
        assert isinstance(client, GroqClient)
        assert client.api_key == "test-api-key"

    @patch('app.genai_assistant.llm_router.settings')
    def test_router_fallback_to_local_gemma_when_no_groq_key(self, mock_settings):
        """Test that LLMRouter falls back to LocalGemmaClient when GROQ_API_KEY not set"""
        mock_settings.GROQ_API_KEY = ""
        mock_settings.LOCAL_GEMMA_URL = "http://localhost:11434"
        router = LLMRouter()
        client = router.get_client("PUBLIC", "enterprise")
        assert isinstance(client, LocalGemmaClient)
        assert client.base_url == "http://localhost:11434"

    @patch('app.genai_assistant.llm_router.settings')
    def test_router_raises_value_error_for_unknown_classification(self, mock_settings):
        """Test that LLMRouter raises ValueError for unknown classification"""
        mock_settings.LOCAL_GEMMA_URL = "http://localhost:11434"
        router = LLMRouter()
        with pytest.raises(ValueError) as exc_info:
            router.get_client("UNKNOWN_CLASS", "enterprise")
        assert "Unknown classification" in str(exc_info.value)


class TestGroqClient:
    """Test suite for GroqClient"""

    def test_groq_client_initialization(self):
        """Test GroqClient initialization"""
        client = GroqClient(api_key="test-key", model="llama3-70b-8192")
        assert client.api_key == "test-key"
        assert client.model == "llama3-70b-8192"

    def test_groq_client_default_model(self):
        """Test GroqClient uses default model"""
        client = GroqClient(api_key="test-key")
        assert client.model == "llama3-70b-8192"


class TestLocalGemmaClient:
    """Test suite for LocalGemmaClient"""

    def test_local_gemma_client_initialization(self):
        """Test LocalGemmaClient initialization"""
        client = LocalGemmaClient(base_url="http://localhost:11434")
        assert client.base_url == "http://localhost:11434"

    def test_local_gemma_client_default_url(self):
        """Test LocalGemmaClient uses default URL"""
        client = LocalGemmaClient()
        assert client.base_url == "http://localhost:11434"
