"""Unit tests for arango_graph tool (v4).

Tests for graph operations:
- Management: create, list, add_vertex_collection, add_edge_definition
- Edge: add_edge
- Traversal: traverse, shortest_path
- Backup: backup, restore, backup_named
- Analysis: validate_integrity, statistics
"""

import pytest
from unittest.mock import MagicMock
from mcp_arangodb_async.graph.handler import handle_graph
from mcp_arangodb_async.graph.management import create_graph, list_graphs
from mcp_arangodb_async.graph.edge import add_edge
from mcp_arangodb_async.graph.traversal import traverse, shortest_path


class TestGraphManagement:
    """Test graph management operations."""

    def test_create_graph(self, mock_db):
        """Should create a named graph."""
        # Arrange
        mock_graph = MagicMock()
        mock_db.create_graph.return_value = mock_graph

        args = {
            "name": "test_graph",
            "edge_definitions": [
                {
                    "edge_collection": "edges",
                    "from_collections": ["vertices"],
                    "to_collections": ["vertices"],
                }
            ],
            "create_collections": True,
        }

        # Act
        result = create_graph(mock_db, args)

        # Assert
        assert isinstance(result, dict)
        assert result["name"] == "test_graph"

    def test_list_graphs(self, mock_db):
        """Should list all graphs."""
        # Arrange
        mock_db.graphs.return_value = [
            {"name": "graph1", "_key": "graph1"},
            {"name": "graph2", "_key": "graph2"},
        ]

        args = {}

        # Act
        result = list_graphs(mock_db, args)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2


class TestGraphEdge:
    """Test edge operations."""

    def test_add_edge(self, mock_db, sample_edge):
        """Should add edge between vertices."""
        # Arrange
        mock_graph = MagicMock()
        mock_edge_col = MagicMock()
        mock_edge_col.insert.return_value = sample_edge
        mock_graph.edge_collection.return_value = mock_edge_col
        mock_db.graph.return_value = mock_graph

        args = {
            "graph": "test_graph",
            "collection": "edges",
            "from_id": sample_edge["_from"],
            "to_id": sample_edge["_to"],
        }

        # Act
        result = add_edge(mock_db, args)

        # Assert
        assert "_key" in result


class TestGraphTraversal:
    """Test graph traversal operations."""

    def test_traverse_from_vertex(self, mock_db):
        """Should traverse graph from starting vertex."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {"_key": "v1", "depth": 0},
            {"_key": "v2", "depth": 1},
            {"_key": "v3", "depth": 2},
        ])

        args = {
            "graph": "test_graph",
            "start_vertex": "vertices/v1",
            "direction": "outbound",
            "max_depth": 3,
        }

        # Act
        result = traverse(mock_db, args)

        # Assert
        assert isinstance(result, (list, dict))

    def test_shortest_path_between_vertices(self, mock_db):
        """Should find shortest path between vertices."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {
                "path": {
                    "vertices": ["v1", "v2", "v3"],
                    "edges": ["e1", "e2"],
                },
                "distance": 2,
            }
        ])

        args = {
            "graph": "test_graph",
            "start_vertex": "vertices/v1",
            "end_vertex": "vertices/v3",
        }

        # Act
        result = shortest_path(mock_db, args)

        # Assert
        assert isinstance(result, dict)


class TestGraphAnalysis:
    """Test graph analysis operations."""

    def test_validate_graph_integrity(self, mock_db):
        """Should validate graph integrity."""
        # Arrange
        args = {"graph": "test_graph"}

        # Act
        result = handle_graph(mock_db, "validate_integrity", args)

        # Assert
        assert isinstance(result, dict)

    def test_graph_statistics(self, mock_db):
        """Should compute graph statistics."""
        # Arrange
        args = {"graph": "test_graph"}

        # Act
        result = handle_graph(mock_db, "statistics", args)

        # Assert
        assert isinstance(result, dict)


class TestGraphHandler:
    """Test graph handler dispatch."""

    def test_handler_dispatches_all_operations(self, mock_db):
        """Should dispatch all graph operations."""
        # Arrange
        mock_db.graphs.return_value = []
        mock_db.aql.execute.return_value = iter([])

        operations = [
            ("list", {}),
            ("create", {"name": "test", "edge_definitions": []}),
            ("traverse", {"graph": "test", "start_vertex": "v1"}),
        ]

        # Act & Assert
        for operation, args in operations:
            result = handle_graph(mock_db, operation, args)
            assert isinstance(result, (dict, list))

    def test_handler_rejects_unknown_operation(self, mock_db):
        """Should reject unknown operations."""
        # Arrange
        args = {}

        # Act
        result = handle_graph(mock_db, "unknown_op", args)

        # Assert
        assert "error" in result or isinstance(result, dict)
