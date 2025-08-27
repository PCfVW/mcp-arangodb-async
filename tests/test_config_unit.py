"""Unit tests for configuration management."""

import pytest
import os
from unittest.mock import patch
from mcp_arangodb_async.config import Config, load_config, validate_config


class TestConfig:
    """Test configuration loading and validation."""

    def test_config_dataclass_creation(self):
        """Test Config dataclass creation."""
        config = Config(
            arango_url="http://localhost:8529",
            database="test_db",
            username="test_user",
            password="test_pass",
            request_timeout=60.0
        )
        
        assert config.arango_url == "http://localhost:8529"
        assert config.database == "test_db"
        assert config.username == "test_user"
        assert config.password == "test_pass"
        assert config.request_timeout == 60.0

    @patch.dict(os.environ, {
        'ARANGO_URL': 'http://test:8529',
        'ARANGO_DB': 'test_database',
        'ARANGO_USERNAME': 'test_user',
        'ARANGO_PASSWORD': 'test_password',
        'ARANGO_TIMEOUT_SEC': '45.0'
    })
    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        config = load_config()
        
        assert config.arango_url == "http://test:8529"
        assert config.database == "test_database"
        assert config.username == "test_user"
        assert config.password == "test_password"
        assert config.request_timeout == 45.0

    @patch.dict(os.environ, {}, clear=True)
    def test_load_config_defaults(self):
        """Test loading configuration with defaults."""
        config = load_config()
        
        assert config.arango_url == "http://localhost:8529"
        assert config.database == "_system"
        assert config.username == "root"
        assert config.password == ""
        assert config.request_timeout == 30.0

    @patch.dict(os.environ, {'ARANGO_TIMEOUT_SEC': 'invalid'})
    def test_load_config_invalid_timeout(self):
        """Test handling invalid timeout value."""
        config = load_config()
        
        assert config.request_timeout == 30.0  # Falls back to default

    def test_validate_config_success(self):
        """Test successful config validation."""
        config = Config(
            arango_url="http://localhost:8529/",  # with trailing slash
            database=" test_db ",  # with whitespace
            username=" root ",  # with whitespace
            password="password"
        )
        
        # Should not raise exception
        validate_config(config)
        
        # Check normalization
        assert config.arango_url == "http://localhost:8529"
        assert config.database == "test_db"
        assert config.username == "root"

    def test_validate_config_empty_url(self):
        """Test validation with empty URL."""
        config = Config(
            arango_url="",
            database="test_db",
            username="root",
            password="password"
        )
        
        with pytest.raises(ValueError, match="ARANGO_URL is required"):
            validate_config(config)

    def test_validate_config_empty_database(self):
        """Test validation with empty database."""
        config = Config(
            arango_url="http://localhost:8529",
            database="",
            username="root",
            password="password"
        )
        
        with pytest.raises(ValueError, match="ARANGO_DB is required"):
            validate_config(config)

    def test_validate_config_empty_username(self):
        """Test validation with empty username."""
        config = Config(
            arango_url="http://localhost:8529",
            database="test_db",
            username="",
            password="password"
        )
        
        with pytest.raises(ValueError, match="ARANGO_USERNAME is required"):
            validate_config(config)
