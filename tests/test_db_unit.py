"""Unit tests for database connection utilities."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from mcp_arangodb_async.db import get_client_and_db, health_check, connect_with_retry
from mcp_arangodb_async.config import Config


class TestDatabaseUtils:
    """Test database connection utilities."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset connection manager to ensure clean state for each test
        from mcp_arangodb_async.db import _connection_manager
        _connection_manager.close()

        self.config = Config(
            arango_url="http://localhost:8529",
            database="test_db",
            username="test_user",
            password="test_pass",
            request_timeout=30.0
        )

    @patch('mcp_arangodb_async.db.ArangoClient')
    def test_get_client_and_db_success(self, mock_arango_client):
        """Test successful client and database connection."""
        # Setup mocks
        mock_client = Mock()
        mock_db = Mock()
        mock_db.version.return_value = "3.11.0"
        mock_client.db.return_value = mock_db
        mock_arango_client.return_value = mock_client
        
        # Execute
        client, db = get_client_and_db(self.config)
        
        # Assert
        assert client == mock_client
        assert db == mock_db
        mock_arango_client.assert_called_once_with(
            hosts="http://localhost:8529",
            request_timeout=30.0
        )
        mock_client.db.assert_called_once_with(
            "test_db",
            username="test_user",
            password="test_pass"
        )
        mock_db.version.assert_called_once()

    @patch('mcp_arangodb_async.db.ArangoClient')
    def test_get_client_and_db_connection_error(self, mock_arango_client):
        """Test connection error handling."""
        # Setup mock to raise exception
        mock_client = Mock()
        mock_db = Mock()
        mock_db.version.side_effect = Exception("Connection failed")
        mock_client.db.return_value = mock_db
        mock_arango_client.return_value = mock_client

        # Execute and assert
        with pytest.raises(Exception, match="Connection failed"):
            get_client_and_db(self.config)

    def test_health_check_success(self):
        """Test successful health check."""
        mock_db = Mock()
        mock_db.version.return_value = "3.11.0"
        
        result = health_check(mock_db)
        
        assert result == {"version": "3.11.0"}
        mock_db.version.assert_called_once()

    def test_health_check_failure(self):
        """Test health check with database error."""
        mock_db = Mock()
        mock_db.version.side_effect = Exception("Database unreachable")
        
        with pytest.raises(Exception, match="Database unreachable"):
            health_check(mock_db)

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.db.get_client_and_db')
    async def test_connect_with_retry_success_first_attempt(self, mock_get_client):
        """Test successful connection on first attempt."""
        mock_client = Mock()
        mock_db = Mock()
        mock_get_client.return_value = (mock_client, mock_db)
        mock_logger = Mock()
        
        client, db = await connect_with_retry(
            self.config,
            retries=3,
            delay_sec=0.1,
            logger=mock_logger
        )
        
        assert client == mock_client
        assert db == mock_db
        mock_get_client.assert_called_once_with(self.config)
        mock_logger.info.assert_called_once()

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.db.get_client_and_db')
    async def test_connect_with_retry_success_second_attempt(self, mock_get_client):
        """Test successful connection on second attempt."""
        mock_client = Mock()
        mock_db = Mock()
        mock_get_client.side_effect = [
            Exception("First attempt failed"),
            (mock_client, mock_db)
        ]
        mock_logger = Mock()
        
        client, db = await connect_with_retry(
            self.config,
            retries=3,
            delay_sec=0.01,  # Short delay for testing
            logger=mock_logger
        )
        
        assert client == mock_client
        assert db == mock_db
        assert mock_get_client.call_count == 2
        assert mock_logger.warning.call_count == 1
        assert mock_logger.info.call_count == 1

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.db.get_client_and_db')
    async def test_connect_with_retry_all_attempts_fail(self, mock_get_client):
        """Test all retry attempts fail."""
        mock_get_client.side_effect = Exception("Connection failed")
        mock_logger = Mock()
        
        client, db = await connect_with_retry(
            self.config,
            retries=2,
            delay_sec=0.01,
            logger=mock_logger
        )
        
        assert client is None
        assert db is None
        assert mock_get_client.call_count == 2
        assert mock_logger.warning.call_count == 2
        assert mock_logger.error.call_count == 1

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.db.get_client_and_db')
    async def test_connect_with_retry_no_logger(self, mock_get_client):
        """Test retry without logger (should not crash)."""
        mock_client = Mock()
        mock_db = Mock()
        mock_get_client.return_value = (mock_client, mock_db)
        
        client, db = await connect_with_retry(self.config, retries=1)
        
        assert client == mock_client
        assert db == mock_db
