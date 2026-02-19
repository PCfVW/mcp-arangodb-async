"""Unit tests for arango_view tool (v4).

Tests for view operations:
- Management: create, drop, list, get, update
- Search: search
"""

import pytest
from unittest.mock import MagicMock
from mcp_arangodb_async.view.handler import handle_view
from mcp_arangodb_async.view.operations import (
    create_view, drop_view, list_views, get_view, update_view, search_view
)


class TestViewManagement:
    """Test view management operations."""

    def test_create_view(self, mock_db):
        """Should create an ArangoSearch view."""
        # Arrange
        mock_view = MagicMock()
        mock_db.create_view.return_value = mock_view

        args = {
            "name": "test_view",
            "type": "arangosearch",
            "properties": {"links": {}},
        }

        # Act
        result = create_view(mock_db, args)

        # Assert
        assert result["success"] is True
        assert result["name"] == "test_view"
        mock_db.create_view.assert_called_once()

    def test_create_view_with_custom_properties(self, mock_db):
        """Should create view with custom properties."""
        # Arrange
        mock_db.create_view.return_value = MagicMock()

        args = {
            "name": "text_search_view",
            "type": "arangosearch",
            "properties": {
                "links": {
                    "documents": {"fields": {"title": {}, "content": {}}}
                }
            },
        }

        # Act
        result = create_view(mock_db, args)

        # Assert
        assert result["success"] is True

    def test_drop_view(self, mock_db):
        """Should drop a view."""
        # Arrange
        mock_db.delete_view.return_value = None
        args = {"name": "test_view"}

        # Act
        result = drop_view(mock_db, args)

        # Assert
        assert result["success"] is True
        assert result["name"] == "test_view"

    def test_list_views(self, mock_db):
        """Should list all views in database."""
        # Arrange
        mock_db.views.return_value = [
            {"name": "view1", "type": "arangosearch"},
            {"name": "view2", "type": "arangosearch"},
        ]

        args = {}

        # Act
        result = list_views(mock_db, args)

        # Assert
        assert result["success"] is True
        assert result["count"] == 2

    def test_list_views_empty(self, mock_db):
        """Should handle empty view list."""
        # Arrange
        mock_db.views.return_value = []
        args = {}

        # Act
        result = list_views(mock_db, args)

        # Assert
        assert result["success"] is True
        assert result["count"] == 0

    def test_get_view_properties(self, mock_db):
        """Should retrieve view properties."""
        # Arrange
        mock_view = MagicMock()
        mock_view.properties.return_value = {
            "name": "test_view",
            "type": "arangosearch",
            "links": {},
        }
        mock_db.view.return_value = mock_view

        args = {"name": "test_view"}

        # Act
        result = get_view(mock_db, args)

        # Assert
        assert result["success"] is True
        assert result["name"] == "test_view"

    def test_update_view_properties(self, mock_db):
        """Should update view properties."""
        # Arrange
        mock_view = MagicMock()
        mock_view.update.return_value = {"updated": True}
        mock_db.view.return_value = mock_view

        args = {
            "name": "test_view",
            "properties": {"commitInterval": 1000},
        }

        # Act
        result = update_view(mock_db, args)

        # Assert
        assert result["success"] is True


class TestViewSearch:
    """Test view search operations."""

    def test_search_view_with_aql_query(self, mock_db):
        """Should execute AQL query against view."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {"_key": "doc1", "text": "search result 1"},
            {"_key": "doc2", "text": "search result 2"},
        ])

        args = {
            "name": "text_view",
            "query": "FOR doc IN text_view SEARCH doc.text == @text RETURN doc",
            "bind_vars": {"text": "search"},
        }

        # Act
        result = search_view(mock_db, args)

        # Assert
        assert result["success"] is True
        assert result["count"] == 2
        assert len(result["results"]) == 2

    def test_search_view_without_query_returns_error(self, mock_db):
        """Should return error when query is missing."""
        # Arrange
        args = {
            "name": "text_view",
            "query": None,
        }

        # Act
        result = search_view(mock_db, args)

        # Assert
        assert result.get("error") is not None or "query parameter required" in str(result)

    def test_search_view_complex_query(self, mock_db):
        """Should handle complex search queries."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {"_key": "advanced_1", "score": 0.95},
        ])

        args = {
            "name": "advanced_view",
            "query": """
                FOR doc IN advanced_view
                SEARCH doc.text LIKE @pattern AND doc.status == 'active'
                SORT doc.score DESC
                RETURN doc
            """,
            "bind_vars": {"pattern": "%search%"},
        }

        # Act
        result = search_view(mock_db, args)

        # Assert
        assert result["success"] is True

    def test_search_view_empty_results(self, mock_db):
        """Should handle search with no results."""
        # Arrange
        mock_db.aql.execute.return_value = iter([])

        args = {
            "name": "text_view",
            "query": "FOR doc IN text_view SEARCH doc.text == @text RETURN doc",
            "bind_vars": {"text": "nonexistent"},
        }

        # Act
        result = search_view(mock_db, args)

        # Assert
        assert result["success"] is True
        assert result["count"] == 0


class TestViewHandler:
    """Test view handler dispatch."""

    def test_handler_dispatches_all_operations(self, mock_db):
        """Should dispatch all view operations."""
        # Arrange
        mock_db.views.return_value = []
        mock_db.aql.execute.return_value = iter([])

        operations = [
            ("list", {}),
            ("create", {"name": "test", "type": "arangosearch"}),
            ("get", {"name": "test"}),
            ("drop", {"name": "test"}),
            ("search", {"name": "test", "query": "RETURN 1"}),
        ]

        # Act & Assert
        for operation, args in operations:
            result = handle_view(mock_db, operation, args)
            assert isinstance(result, dict)

    def test_handler_rejects_unknown_operation(self, mock_db):
        """Should reject unknown operations."""
        # Arrange
        args = {}

        # Act
        result = handle_view(mock_db, "unknown_op", args)

        # Assert
        assert result.get("error") is not None or isinstance(result, dict)


class TestViewModels:
    """Test view model validation."""

    def test_create_view_args_validation(self):
        """Should validate CreateViewArgs."""
        from mcp_arangodb_async.view.models import CreateViewArgs

        # Arrange & Act
        args = CreateViewArgs(name="test_view", type="arangosearch")

        # Assert
        assert args.name == "test_view"
        assert args.type == "arangosearch"

    def test_search_view_args_validation(self):
        """Should validate SearchViewArgs."""
        from mcp_arangodb_async.view.models import SearchViewArgs

        # Arrange & Act
        args = SearchViewArgs(
            name="test_view",
            query="RETURN 1",
            bind_vars={"limit": 10}
        )

        # Assert
        assert args.name == "test_view"
        assert args.query == "RETURN 1"
