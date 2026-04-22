import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone
from app.simulation.digital_twin import DigitalTwinSimulator, PlaybookAction, SimulationResult


class TestDigitalTwinSimulator:
    """Digital Twin Simulator Tests"""

    @pytest.mark.asyncio
    async def test_simulate_action_returns_simulation_result_with_valid_impact_score(self):
        """Test simulate_action() returns SimulationResult with 0.0 <= impact_score <= 1.0"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetch.return_value = []

        simulator = DigitalTwinSimulator(mock_pool)
        action = PlaybookAction(
            action_id="act-1",
            action_type="BLOCK_IP",
            target="192.168.1.1",
            reversibility="IRREVERSIBLE",
            description="Block malicious IP"
        )
        tenant_id = uuid4()

        result = await simulator.simulate_action(action, tenant_id)

        assert isinstance(result, SimulationResult)
        assert 0.0 <= result.impact_score <= 1.0

    @pytest.mark.asyncio
    async def test_simulate_action_is_not_a_pass_stub(self):
        """Test simulate_action() is NOT a pass stub (call it and inspect return type)"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetch.return_value = []

        simulator = DigitalTwinSimulator(mock_pool)
        action = PlaybookAction(
            action_id="act-1",
            action_type="BLOCK_IP",
            target="192.168.1.1",
            reversibility="IRREVERSIBLE",
            description="Block malicious IP"
        )
        tenant_id = uuid4()

        result = await simulator.simulate_action(action, tenant_id)

        # Verify it returns a proper SimulationResult, not None or stub
        assert result is not None
        assert hasattr(result, 'impact_score')
        assert hasattr(result, 'n_fp')
        assert hasattr(result, 'n_total')
        assert hasattr(result, 'recommendation')
        assert result.replay_window_minutes == 30
        assert result.simulated_at is not None

    @pytest.mark.asyncio
    async def test_empty_history_returns_impact_score_1_0_conservative(self):
        """Test empty history returns impact_score=1.0 (conservative)"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetch.return_value = []

        simulator = DigitalTwinSimulator(mock_pool)
        action = PlaybookAction(
            action_id="act-1",
            action_type="BLOCK_IP",
            target="192.168.1.1",
            reversibility="IRREVERSIBLE",
            description="Block malicious IP"
        )
        tenant_id = uuid4()

        result = await simulator.simulate_action(action, tenant_id)

        assert result.impact_score == 1.0
        assert result.n_fp == 0
        assert result.n_total == 0
        assert result.recommendation == "BLOCK_PENDING_INVESTIGATION"

    @pytest.mark.asyncio
    async def test_impact_score_ge_0_05_returns_block_pending_investigation(self):
        """Test impact_score >= 0.05 returns BLOCK_PENDING_INVESTIGATION"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Mock events: 10 total, 1 would be incorrectly blocked (10% FP rate)
        mock_row = MagicMock()
        mock_row.get.side_effect = lambda key: {
            "source_ip": "192.168.1.1",
            "indicator_value": "malicious.com",
            "status": "BENIGN"
        }.get(key)
        mock_conn.fetch.return_value = [mock_row] * 10

        simulator = DigitalTwinSimulator(mock_pool)
        action = PlaybookAction(
            action_id="act-1",
            action_type="BLOCK_IP",
            target="192.168.1.1",
            reversibility="IRREVERSIBLE",
            description="Block malicious IP"
        )
        tenant_id = uuid4()

        result = await simulator.simulate_action(action, tenant_id)

        assert result.impact_score >= 0.05
        assert result.recommendation == "BLOCK_PENDING_INVESTIGATION"

    @pytest.mark.asyncio
    async def test_impact_score_lt_0_05_returns_present_to_analyst(self):
        """Test impact_score < 0.05 returns PRESENT_TO_ANALYST_FOR_APPROVAL"""
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn

        # Mock events: 100 total, 2 would be incorrectly blocked (2% FP rate)
        mock_row_confirmed = MagicMock()
        mock_row_confirmed.get.side_effect = lambda key: {
            "source_ip": "192.168.1.1",
            "indicator_value": "malicious.com",
            "status": "CONFIRMED_THREAT"
        }.get(key)

        mock_row_benign_diff = MagicMock()
        mock_row_benign_diff.get.side_effect = lambda key: {
            "source_ip": "192.168.1.2",
            "indicator_value": "malicious.com",
            "status": "BENIGN"
        }.get(key)

        mock_conn.fetch.return_value = [mock_row_confirmed] * 98 + [mock_row_benign_diff] * 2

        simulator = DigitalTwinSimulator(mock_pool)
        action = PlaybookAction(
            action_id="act-1",
            action_type="BLOCK_IP",
            target="192.168.1.1",
            reversibility="IRREVERSIBLE",
            description="Block malicious IP"
        )
        tenant_id = uuid4()

        result = await simulator.simulate_action(action, tenant_id)

        assert result.impact_score < 0.05
        assert result.recommendation == "PRESENT_TO_ANALYST_FOR_APPROVAL"

    def test_block_ip_action_matches_only_target_ip_in_history(self):
        """Test BLOCK_IP action matches only the target IP in history"""
        simulator = DigitalTwinSimulator(MagicMock())
        action = PlaybookAction(
            action_id="act-1",
            action_type="BLOCK_IP",
            target="192.168.1.1",
            reversibility="IRREVERSIBLE",
            description="Block malicious IP"
        )

        # Event with matching IP
        event_match = MagicMock()
        event_match.get.side_effect = lambda key: "192.168.1.1" if key == "source_ip" else None

        # Event with different IP
        event_no_match = MagicMock()
        event_no_match.get.side_effect = lambda key: "192.168.1.2" if key == "source_ip" else None

        assert simulator._would_block(action, event_match) is True
        assert simulator._would_block(action, event_no_match) is False

    def test_is_confirmed_threat(self):
        """Test _is_confirmed_threat correctly identifies confirmed threats"""
        simulator = DigitalTwinSimulator(MagicMock())

        event_confirmed = MagicMock()
        event_confirmed.get.return_value = "CONFIRMED_THREAT"

        event_elevated = MagicMock()
        event_elevated.get.return_value = "ELEVATED"

        event_benign = MagicMock()
        event_benign.get.return_value = "BENIGN"

        assert simulator._is_confirmed_threat(event_confirmed) is True
        assert simulator._is_confirmed_threat(event_elevated) is True
        assert simulator._is_confirmed_threat(event_benign) is False
