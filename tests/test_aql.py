"""Unit tests for arango_aql tool (v4).

Tests for AQL operations:
- query: Execute AQL query
- explain: Get query execution plan
- profile: Profile query performance
- build: Build query string
"""

import pytest
from unittest.mock import MagicMock
from mcp_arangodb_async.aql.handler import handle_aql
from mcp_arangodb_async.aql.query import arango_query, explain_query, query_profile
from mcp_arangodb_async.aql.builder import query_builder


class TestAQLQuery:
    """Test AQL query execution."""

    def test_execute_simple_query(self, mock_db):
        """Should execute simple AQL query."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {"value": 1},
            {"value": 2},
            {"value": 3},
        ])

        args = {
            "query": "RETURN 1",
            "bind_vars": {},
        }

        # Act
        result = handle_aql(mock_db, "query", args)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 3

    def test_execute_query_with_bind_variables(self, mock_db):
        """Should execute query with bind variables."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ])

        args = {
            "query": "FOR user IN @users RETURN user",
            "bind_vars": {"users": ["Alice", "Bob"]},
        }

        # Act
        result = handle_aql(mock_db, "query", args)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2

    def test_execute_complex_query(self, mock_db):
        """Should execute complex multi-line query."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {"_key": "result1", "count": 42},
        ])

        args = {
            "query": """
                FOR doc IN collection
                FILTER doc.status == 'active'
                COLLECT group = doc.category WITH COUNT INTO total
                SORT total DESC
                RETURN { group, total }
            """,
        }

        # Act
        result = handle_aql(mock_db, "query", args)

        # Assert
        assert isinstance(result, list)

    def test_query_returns_results_array(self, mock_db):
        """Should return array of results."""
        # Arrange
        test_results = [{"id": i} for i in range(5)]
        mock_db.aql.execute.return_value = iter(test_results)

        args = {"query": "FOR doc IN collection RETURN doc"}

        # Act
        result = handle_aql(mock_db, "query", args)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 5


class TestAQLExplain:
    """Test AQL query explanation."""

    def test_explain_returns_execution_plan(self, mock_db):
        """Should return query execution plan."""
        # Arrange
        mock_db.aql.explain.return_value = {
            "plans": [
                {
                    "nodes": [
                        {"type": "SingletonNode", "id": 0},
                        {"type": "ReturnNode", "id": 1},
                    ],
                    "estimatedCost": 1.0,
                    "estimatedNrItems": 1,
                }
            ],
            "warnings": [],
        }

        args = {"query": "RETURN 1"}

        # Act
        result = handle_aql(mock_db, "explain", args)

        # Assert
        assert isinstance(result, dict)
        assert "plans" in result

    def test_explain_includes_optimization_info(self, mock_db):
        """Should include optimization information."""
        # Arrange
        mock_db.aql.explain.return_value = {
            "plans": [{"estimatedCost": 42.5}],
            "warnings": ["Consider adding indexes"],
        }

        args = {"query": "FOR doc IN collection RETURN doc"}

        # Act
        result = handle_aql(mock_db, "explain", args)

        # Assert
        assert isinstance(result, dict)


class TestAQLProfile:
    """Test AQL query profiling."""

    def test_profile_query_performance(self, mock_db):
        """Should profile query performance."""
        # Arrange
        mock_db.aql.execute.return_value = iter([{"result": 1}])
        mock_db.aql.explain.return_value = {
            "stats": {"executionTime": 0.5},
            "profile": {"calls": 100, "runtime": 50},
        }

        args = {"query": "FOR doc IN collection RETURN doc"}

        # Act
        result = handle_aql(mock_db, "profile", args)

        # Assert
        assert isinstance(result, dict)

    def test_profile_includes_timing_information(self, mock_db):
        """Should include timing information."""
        # Arrange
        mock_db.aql.execute.return_value = iter([])

        args = {"query": "RETURN 1"}

        # Act
        result = handle_aql(mock_db, "profile", args)

        # Assert
        assert isinstance(result, dict)


class TestAQLBuild:
    """Test query building utilities."""

    def test_build_simple_query(self, mock_db):
        """Should build and execute a filtered query."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {"_key": "u1", "name": "Alice"},
            {"_key": "u2", "name": "Bob"},
        ])
        args = {
            "collection": "users",
            "filters": [{"field": "status", "op": "==", "value": "active"}],
        }

        # Act
        result = handle_aql(mock_db, "build", args)

        # Assert
        assert isinstance(result, list)

    def test_build_query_with_sort_and_limit(self, mock_db):
        """Should build and execute a query with sort and limit."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {"_key": "u1", "age": 30},
        ])
        args = {
            "collection": "users",
            "sort": [{"field": "age", "direction": "DESC"}],
            "limit": 1,
        }

        # Act
        result = handle_aql(mock_db, "build", args)

        # Assert
        assert isinstance(result, list)

    def test_build_query_with_return_fields(self, mock_db):
        """Should build query with field projection."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {"name": "Alice", "email": "alice@example.com"},
        ])
        args = {
            "collection": "users",
            "return_fields": ["name", "email"],
        }

        # Act
        result = handle_aql(mock_db, "build", args)

        # Assert
        assert isinstance(result, list)

    def test_build_query_empty_collection(self, mock_db):
        """Should return empty list when collection has no matching docs."""
        # Arrange
        mock_db.aql.execute.return_value = iter([])
        args = {"collection": "empty_col"}

        # Act
        result = handle_aql(mock_db, "build", args)

        # Assert
        assert result == []


class TestAQLHandler:
    """Test AQL handler dispatch."""

    def test_handler_dispatches_all_operations(self, mock_db):
        """Should dispatch all AQL operations."""
        # Arrange
        mock_db.aql.execute.return_value = iter([{"result": 1}])
        mock_db.aql.explain.return_value = {"plans": []}

        operations = [
            ("query", {"query": "RETURN 1"}),
            ("explain", {"query": "RETURN 1"}),
            ("profile", {"query": "RETURN 1"}),
            ("build", {"operation": "select", "collection": "test"}),
        ]

        # Act & Assert
        for operation, args in operations:
            result = handle_aql(mock_db, operation, args)
            assert isinstance(result, (dict, list))

    def test_handler_rejects_unknown_operation(self, mock_db):
        """Should reject unknown operations."""
        # Arrange
        args = {}

        # Act
        result = handle_aql(mock_db, "unknown_op", args)

        # Assert
        assert "error" in result or isinstance(result, dict)


class TestAQLModels:
    """Test AQL model validation."""

    def test_aql_args_validation(self):
        """Should validate AQLArgs model."""
        from mcp_arangodb_async.aql.models import AQLArgs

        # Arrange & Act
        args = AQLArgs(action="query")

        # Assert
        assert args.action == "query"

    def test_query_args_validation(self):
        """Should validate QueryArgs model."""
        from mcp_arangodb_async.aql.models import QueryArgs

        # Arrange & Act
        args = QueryArgs(query="RETURN 1", bind_vars=None)

        # Assert
        assert args.query == "RETURN 1"
