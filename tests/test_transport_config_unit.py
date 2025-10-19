"""Unit tests for transport configuration (Phase 2)."""

import pytest
from mcp_arangodb_async.transport_config import TransportConfig


class TestTransportConfig:
    """Test TransportConfig dataclass and validation."""

    def test_default_config(self):
        """Test default configuration values."""
        config = TransportConfig()
        
        assert config.transport == "stdio"
        assert config.http_host == "0.0.0.0"
        assert config.http_port == 8000
        assert config.http_stateless is False
        assert config.http_cors_origins == ["*"]

    def test_stdio_config(self):
        """Test stdio transport configuration."""
        config = TransportConfig(transport="stdio")
        
        assert config.transport == "stdio"
        # HTTP settings should still have defaults even for stdio
        assert config.http_port == 8000

    def test_http_config_basic(self):
        """Test basic HTTP configuration."""
        config = TransportConfig(
            transport="http",
            http_host="127.0.0.1",
            http_port=9000
        )
        
        assert config.transport == "http"
        assert config.http_host == "127.0.0.1"
        assert config.http_port == 9000
        assert config.http_stateless is False
        assert config.http_cors_origins == ["*"]

    def test_http_config_stateless(self):
        """Test HTTP configuration with stateless mode."""
        config = TransportConfig(
            transport="http",
            http_stateless=True
        )
        
        assert config.transport == "http"
        assert config.http_stateless is True

    def test_http_config_custom_cors(self):
        """Test HTTP configuration with custom CORS origins."""
        cors_origins = ["https://app.example.com", "https://admin.example.com"]
        config = TransportConfig(
            transport="http",
            http_cors_origins=cors_origins
        )
        
        assert config.transport == "http"
        assert config.http_cors_origins == cors_origins

    def test_http_config_all_options(self):
        """Test HTTP configuration with all options specified."""
        config = TransportConfig(
            transport="http",
            http_host="0.0.0.0",
            http_port=8080,
            http_stateless=True,
            http_cors_origins=["https://example.com"]
        )
        
        assert config.transport == "http"
        assert config.http_host == "0.0.0.0"
        assert config.http_port == 8080
        assert config.http_stateless is True
        assert config.http_cors_origins == ["https://example.com"]

    def test_invalid_transport_type(self):
        """Test validation of invalid transport type."""
        with pytest.raises(ValueError, match="Invalid transport"):
            TransportConfig(transport="websocket")  # type: ignore

    def test_invalid_port_too_low(self):
        """Test validation of port number too low."""
        with pytest.raises(ValueError, match="Invalid HTTP port"):
            TransportConfig(http_port=0)

    def test_invalid_port_too_high(self):
        """Test validation of port number too high."""
        with pytest.raises(ValueError, match="Invalid HTTP port"):
            TransportConfig(http_port=70000)

    def test_valid_port_boundaries(self):
        """Test valid port number boundaries."""
        # Port 1 (minimum)
        config1 = TransportConfig(http_port=1)
        assert config1.http_port == 1
        
        # Port 65535 (maximum)
        config2 = TransportConfig(http_port=65535)
        assert config2.http_port == 65535

    def test_frozen_dataclass(self):
        """Test that TransportConfig is immutable (frozen)."""
        config = TransportConfig()
        
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            config.transport = "http"  # type: ignore

    def test_cors_origins_none_becomes_wildcard(self):
        """Test that None CORS origins becomes wildcard."""
        config = TransportConfig(http_cors_origins=None)
        
        assert config.http_cors_origins == ["*"]

    def test_cors_origins_empty_list(self):
        """Test that empty CORS origins list is preserved."""
        config = TransportConfig(http_cors_origins=[])
        
        assert config.http_cors_origins == []


class TestTransportConfigUseCases:
    """Test real-world use cases for TransportConfig."""

    def test_local_development_stdio(self):
        """Test configuration for local development with stdio."""
        config = TransportConfig()
        
        assert config.transport == "stdio"

    def test_local_development_http(self):
        """Test configuration for local development with HTTP."""
        config = TransportConfig(
            transport="http",
            http_host="127.0.0.1",
            http_port=8000
        )
        
        assert config.transport == "http"
        assert config.http_host == "127.0.0.1"
        assert config.http_cors_origins == ["*"]  # Permissive for dev

    def test_production_single_instance(self):
        """Test configuration for production single-instance deployment."""
        config = TransportConfig(
            transport="http",
            http_host="0.0.0.0",
            http_port=8000,
            http_stateless=False,  # Stateful for single instance
            http_cors_origins=["https://app.example.com"]
        )
        
        assert config.transport == "http"
        assert config.http_stateless is False
        assert config.http_cors_origins == ["https://app.example.com"]

    def test_production_multi_instance(self):
        """Test configuration for production multi-instance deployment."""
        config = TransportConfig(
            transport="http",
            http_host="0.0.0.0",
            http_port=8000,
            http_stateless=True,  # Stateless for horizontal scaling
            http_cors_origins=["https://app.example.com", "https://admin.example.com"]
        )
        
        assert config.transport == "http"
        assert config.http_stateless is True
        assert len(config.http_cors_origins) == 2

    def test_docker_deployment(self):
        """Test configuration for Docker deployment."""
        config = TransportConfig(
            transport="http",
            http_host="0.0.0.0",  # Bind to all interfaces in container
            http_port=8000,
            http_cors_origins=["*"]  # Can be restricted via env var
        )
        
        assert config.transport == "http"
        assert config.http_host == "0.0.0.0"

    def test_kubernetes_deployment(self):
        """Test configuration for Kubernetes deployment."""
        config = TransportConfig(
            transport="http",
            http_host="0.0.0.0",
            http_port=8000,
            http_stateless=True,  # Required for K8s horizontal scaling
            http_cors_origins=["https://app.example.com"]
        )
        
        assert config.transport == "http"
        assert config.http_stateless is True

