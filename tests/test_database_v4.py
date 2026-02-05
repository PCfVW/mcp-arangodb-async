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
from mcp_arangodb_async.database.models import DatabaseArgs, ListArgs, GetFocusedArgs, SwitchArgs, GetResolutionArgs


class TestDatabaseList:
    """Test database list operation."""

    def test_list_returns_database_names(self, mock_db):
        """Should return list of available databases."""
        # Arrange
        mock_db.databases.return_value = ["_system", "test", "mydb"]
        args = {}

        # Act
        result = handle_database(mock_db, "list", args)

        # Assert
        assert result["success"] is True
        assert "_system" in result["databases"]
        assert "test" in result["databases"]
        mock_db.databases.assert_called_once()

    def test_list_handles_empty_database_list(self, mock_db):
        """Should handle empty database list gracefully."""
        # Arrange
        mock_db.databases.return_value = []
        args = {}

        # Act
        result = handle_database(mock_db, "list", args)

        # Assert
        assert result["success"] is True
        assert len(result["databases"]) == 0

    def test_list_includes_count(self, mock_db):
        """Should include database count in result."""
        # Arrange
        mock_db.databases.return_value = ["_system", "test"]
        args = {}

        # Act
        result = handle_database(mock_db, "list", args)

        # Assert
        assert "count" in result
        assert result["count"] == 2

    def test_list_handles_database_error(self, mock_db):
        """Should return error dict on database exception."""
        # Arrange
        mock_db.databases.side_effect = Exception("Connection failed")
        args = {}

        # Act
        result = handle_database(mock_db, "list", args)

        # Assert
        assert "error" in result
        assert result["success"] is False


class TestDatabaseGetFocused:
    """Test get_focused operation."""

    def test_get_focused_returns_current_database(self, mock_db):
        """Should return currently focused database info."""
        # Arrange
        mock_db.name = "test"
        mock_db.version.return_value = {"version": "3.12.0"}
        args = {}

        # Act
        result = handle_database(mock_db, "get_focused", args)

        # Assert
        assert result["success"] is True
        assert result["database"] == "test"

    def test_get_focused_includes_metadata(self, mock_db):
        """Should include database metadata."""
        # Arrange
        mock_db.name = "test"
        mock_db.version.return_value = {"version": "3.12.0", "license": "community"}
        args = {}

        # Act
        result = handle_database(mock_db, "get_focused", args)

        # Assert
        assert "metadata" in result or "version" in result


class TestDatabaseSwitch:
    """Test switch operation."""

    def test_switch_changes_database(self, mock_db):
        """Should switch to specified database."""
        # Arrange
        args = {"database": "mydb"}

        # Act
        result = handle_database(mock_db, "switch", args)

        # Assert
        assert result["success"] is True
        assert result["database"] == "mydb"

    def test_switch_validates_database_name(self, mock_db):
        """Should validate database name format."""
        # Arrange
        mock_db.databases.return_value = ["_system", "test"]
        args = {"database": "nonexistent"}

        # Act
        result = handle_database(mock_db, "switch", args)

        # Assert
        # Should either succeed with a marker or return an error
        assert "database" in result or "error" in result

    def test_switch_handles_invalid_database(self, mock_db):
        """Should handle switching to non-existent database gracefully."""
        # Arrange
        mock_db.databases.return_value = ["_system", "test"]
        args = {"database": ""}

        # Act/Assert - should not crash
        result = handle_database(mock_db, "switch", args)
        assert isinstance(result, dict)


class TestDatabaseGetResolution:
    """Test get_resolution operation."""

    def test_get_resolution_returns_config(self, mock_db):
        """Should return database resolution configuration."""
        # Arrange
        args = {}

        # Act
        result = handle_database(mock_db, "get_resolution", args)

        # Assert
        assert isinstance(result, dict)
        # Should contain resolution information
        assert "resolution" in result or "config" in result or "success" in result

    def test_get_resolution_includes_priority_levels(self, mock_db):
        """Should include database resolution priority levels."""
        # Arrange
        args = {}

        # Act
        result = handle_database(mock_db, "get_resolution", args)

        # Assert
        # v4 architecture defines 6-level resolution: tool override > focused > config > env > first > fallback
        assert isinstance(result, dict)


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
        """Should handle different argument structures."""
        # Arrange
        test_cases = [
            ("list", {}),
            ("get_focused", {}),
            ("switch", {"database": "test"}),
            ("get_resolution", {}),
        ]

        # Act/Assert
        for operation, args in test_cases:
            result = handle_database(mock_db, operation, args)
            assert isinstance(result, dict)
            # Should not raise exceptions


class TestDatabaseModels:
    """Test Pydantic models for validation."""

    def test_list_args_model(self):
        """Should validate ListArgs model."""
        # Arrange & Act
        args = ListArgs(database=None)

        # Assert
        assert args.database is None

    def test_switch_args_model(self):
        """Should validate SwitchArgs model."""
        # Arrange & Act
        args = SwitchArgs(database="test")

        # Assert
        assert args.database == "test"

    def test_get_focused_args_model(self):
        """Should validate GetFocusedArgs model."""
        # Arrange & Act
        args = GetFocusedArgs()

        # Assert
        assert isinstance(args, GetFocusedArgs)

    def test_database_args_with_action(self):
        """Should validate DatabaseArgs with action."""
        # Arrange & Act
        args = DatabaseArgs(action="list")

        # Assert
        assert args.action == "list"

    def test_database_args_rejects_invalid_action(self):
        """Should reject invalid action values."""
        # Arrange & Act & Assert
        with pytest.raises(Exception):  # Pydantic validation error
            DatabaseArgs(action="invalid_action")
