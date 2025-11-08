"""
Test suite for API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.core.ai_engine import AIEngine

client = TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints"""

    def test_basic_health_check(self):
        """Test basic health check endpoint"""
        response = client.get("/api/v1/health/")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "service" in data
        assert "version" in data

    def test_liveness_probe(self):
        """Test liveness probe endpoint"""
        response = client.get("/api/v1/health/liveness")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data

    @patch('app.api.endpoints.health.AIEngine')
    def test_readiness_probe_with_models(self, mock_ai_engine_class):
        """Test readiness probe with available models"""
        # Mock AI engine with available models
        mock_engine = Mock()
        mock_engine.get_available_models.return_value = [
            {"model": "gpt-3.5", "provider": "openai"}
        ]
        mock_ai_engine_class.return_value = mock_engine

        response = client.get("/api/v1/health/readiness")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert "models_available" in data
        assert data["models_available"] > 0

    @patch('app.api.endpoints.health.AIEngine')
    def test_readiness_probe_no_models(self, mock_ai_engine_class):
        """Test readiness probe with no available models"""
        # Mock AI engine with no models
        mock_engine = Mock()
        mock_engine.get_available_models.return_value = []
        mock_ai_engine_class.return_value = mock_engine

        response = client.get("/api/v1/health/readiness")
        assert response.status_code == 503


class TestModeEndpoints:
    """Test mode management endpoints"""

    def test_get_available_modes(self):
        """Test getting available modes"""
        response = client.get("/api/v1/modes/")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "modes" in data["data"]
        assert "count" in data["data"]

        modes = data["data"]["modes"]
        mode_names = [mode["name"] for mode in modes]

        # Check that all expected modes are present
        expected_modes = ["creative", "precise", "teach", "code", "analyze"]
        for mode in expected_modes:
            assert mode in mode_names

    def test_get_mode_details_valid(self):
        """Test getting details for a valid mode"""
        response = client.get("/api/v1/modes/creative")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["name"] == "creative"

    def test_get_mode_details_invalid(self):
        """Test getting details for an invalid mode"""
        response = client.get("/api/v1/modes/invalid_mode")
        assert response.status_code == 404

    def test_validate_mode_valid(self):
        """Test validating a valid mode"""
        response = client.get("/api/v1/modes/validate/creative")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_valid"] is True
        assert "creative" in data["data"]["valid_modes"]

    def test_validate_mode_invalid(self):
        """Test validating an invalid mode"""
        response = client.get("/api/v1/modes/validate/invalid_mode")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["is_valid"] is False

    def test_get_mode_examples_valid(self):
        """Test getting examples for a valid mode"""
        response = client.get("/api/v1/modes/examples/creative")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "description" in data["data"]
        assert "prompts" in data["data"]
        assert len(data["data"]["prompts"]) > 0

    def test_get_mode_examples_invalid(self):
        """Test getting examples for an invalid mode"""
        response = client.get("/api/v1/modes/examples/invalid_mode")
        assert response.status_code == 404


class TestChatEndpoints:
    """Test chat endpoints"""

    def test_chat_message_invalid_request(self):
        """Test chat message with invalid request"""
        # Missing required fields
        response = client.post("/api/v1/chat/", json={})
        assert response.status_code == 422  # Validation error

    def test_chat_message_invalid_mode(self):
        """Test chat message with invalid mode"""
        request_data = {
            "message": "Hello, world!",
            "mode": "invalid_mode"
        }
        response = client.post("/api/v1/chat/", json=request_data)
        assert response.status_code == 400

    @patch('app.api.endpoints.chat.AIEngine')
    def test_chat_message_valid_request(self, mock_ai_engine_class):
        """Test chat message with valid request"""
        # Mock AI engine response
        mock_engine = Mock()
        mock_engine.process_message.return_value = {
            "response": "Hello! How can I help you today?",
            "conversation_id": "test-conversation-id",
            "mode_used": "precise",
            "model_used": "gpt-3.5",
            "request_id": "test-request-id",
            "metadata": {
                "response_time_ms": 1000,
                "tokens_used": 50,
                "confidence_score": 0.95
            }
        }
        mock_ai_engine_class.return_value = mock_engine

        request_data = {
            "message": "Hello, world!",
            "mode": "precise"
        }
        response = client.post("/api/v1/chat/", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["response"] == "Hello! How can I help you today?"
        assert data["data"]["mode_used"] == "precise"

    def test_get_conversation_history_not_found(self):
        """Test getting conversation history for non-existent conversation"""
        response = client.get("/api/v1/chat/conversations/non-existent/history")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["data"]["history"] == []

    def test_get_conversation_summary_not_found(self):
        """Test getting conversation summary for non-existent conversation"""
        response = client.get("/api/v1/chat/conversations/non-existent/summary")
        assert response.status_code == 404


class TestRootEndpoint:
    """Test root endpoint"""

    def test_root_endpoint(self):
        """Test root endpoint returns basic info"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data


if __name__ == "__main__":
    pytest.main([__file__])