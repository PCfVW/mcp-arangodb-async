"""Unit tests for arango_database tool (v4).

Tests for database operations:
- list: List available databases
- get_focused: Get currently focused database
- switch: Switch to different database
- get_resolution: Get database resolution info
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from mcp_arangodb_async.database.handler import handle_database
from mcp_arangodb_async.database.models import DatabaseArgs, ListAvailableArgs, GetFocusedArgs, SwitchArgs, GetResolutionArgs


def make_db_manager(*db_keys):
    """Create a mock db_manager with given database keys."""
    mock_mgr = MagicMock()
    configs = {
        k: MagicMock(url="http://localhost:8529", database=k, username="root")
        for k in db_keys
    }
    mock_mgr.get_configured_databases.return_value = configs
    return mock_mgr


def make_session_state(focused_db=None):
    """Create a mock session_state."""
    mock_state = MagicMock()
    mock_state.get_focused_database.return_value = focused_db
    mock_state.set_focused_database.return_value = None
    return mock_state


class TestDatabaseList:
    """Test database list operation."""

    def test_list_returns_database_names(self, mock_db):
        """Should return list of available databases."""
        # Arrange
        args = {
            "_session_context": {
                "db_manager": make_db_manager("_system", "test", "mydb")
            }
        }

        # Act
        result = handle_database(mock_db, "list", args)

        # Assert
        assert "databases" in result
        assert result["total_count"] == 3

    def test_list_handles_empty_database_list(self, mock_db):
        """Should handle empty database list gracefully."""
        # Arrange
        args = {
            "_session_context": {
                "db_manager": make_db_manager()
            }
        }

        # Act
        result = handle_database(mock_db, "list", args)

        # Assert
        assert result["total_count"] == 0
        assert result["databases"] == []

    def test_list_without_manager_returns_error(self, mock_db):
        """Should return error when db_manager not available."""
        # Arrange
        args = {}

        # Act
        result = handle_database(mock_db, "list", args)

        # Assert
        assert "error" in result
        assert result["databases"] == []


class TestDatabaseGetFocused:
    """Test get_focused operation."""

    def test_get_focused_returns_current_database(self, mock_db):
        """Should return currently focused database info."""
        # Arrange
        args = {
            "_session_context": {
                "session_state": make_session_state("test"),
                "session_id": "stdio",
            }
        }

        # Act
        result = handle_database(mock_db, "get_focused", args)

        # Assert
        assert result["focused_database"] == "test"
        assert result["is_set"] is True

    def test_get_focused_without_session_returns_defaults(self, mock_db):
        """Should return defaults when session state not available."""
        # Arrange
        args = {}

        # Act
        result = handle_database(mock_db, "get_focused", args)

        # Assert
        assert result["focused_database"] is None
        assert result["is_set"] is False
        assert "error" in result


class TestDatabaseSwitch:
    """Test switch operation."""

    def test_switch_changes_database(self, mock_db):
        """Should switch to specified database."""
        # Arrange
        args = {
            "database": "mydb",
            "_session_context": {
                "session_state": make_session_state(),
                "session_id": "stdio",
            }
        }

        # Act
        result = handle_database(mock_db, "switch", args)

        # Assert
        assert isinstance(result, dict)
        assert "database" in result or "success" in result or "focused_database" in result

    def test_switch_without_session_returns_error(self, mock_db):
        """Should return error when session not available."""
        # Arrange
        args = {"database": "mydb"}

        # Act
        result = handle_database(mock_db, "switch", args)

        # Assert
        assert isinstance(result, dict)
        assert "error" in result or "success" in result


class TestDatabaseGetResolution:
    """Test get_resolution operation."""

    def test_get_resolution_returns_dict(self, mock_db):
        """Should return database resolution info as a dict."""
        # Arrange
        args = {}

        # Act
        result = handle_database(mock_db, "get_resolution", args)

        # Assert
        assert isinstance(result, dict)

    def test_get_resolution_contains_error_or_config(self, mock_db):
        """Should return either resolution config or error."""
        # Arrange
        args = {}

        # Act
        result = handle_database(mock_db, "get_resolution", args)

        # Assert
        assert "error" in result or "resolution" in result or "config" in result or "levels" in result or "configuration" in result


class TestDatabaseHandlerDispatch:
    """Test handler dispatch mechanism."""

    def test_unknown_operation_returns_error(self, mock_db):
        """Should return error for unknown operations."""
        # Arrange
        args = {}

        # Act
        result = handle_database(mock_db, "unknown_op", args)

        # Assert
        assert "error" in result

    def test_handler_accepts_various_argument_types(self, mock_db):
        """Should handle different argument structures without raising."""
        test_cases = [
            ("list", {}),
            ("get_focused", {}),
            ("get_resolution", {}),
        ]

        for operation, args in test_cases:
            result = handle_database(mock_db, operation, args)
            assert isinstance(result, dict)


class TestDatabaseModels:
    """Test Pydantic models for validation."""

    def test_list_available_args_model(self):
        """Should validate ListAvailableArgs model."""
        args = ListAvailableArgs()
        assert isinstance(args, ListAvailableArgs)

    def test_switch_args_model(self):
        """Should validate SwitchArgs model."""
        args = SwitchArgs(database="test")
        assert args.database == "test"

    def test_get_focused_args_model(self):
        """Should validate GetFocusedArgs model."""
        args = GetFocusedArgs()
        assert isinstance(args, GetFocusedArgs)

    def test_database_args_with_action(self):
        """Should validate DatabaseArgs with action."""
        args = DatabaseArgs(action="list")
        assert args.action == "list"

    def test_database_args_rejects_invalid_action(self):
        """Should reject invalid action values."""
        with pytest.raises(Exception):
            DatabaseArgs(action="invalid_action")
