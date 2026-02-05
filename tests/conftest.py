"""Pytest configuration and shared fixtures for v4 tool tests.

This module provides:
- Database connection fixtures
- Mock object factories
- Test data generators
- Common test utilities
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any


@pytest.fixture
def mock_db():
    """Create a mock ArangoDB database connection."""
    db = MagicMock()
    db.version.return_value = {"version": "3.12.0", "license": "community"}
    return db


@pytest.fixture
def mock_collection():
    """Create a mock ArangoDB collection."""
    collection = MagicMock()
    collection.name = "test_collection"
    collection.count.return_value = 5
    return collection


@pytest.fixture
def mock_graph():
    """Create a mock ArangoDB graph."""
    graph = MagicMock()
    graph.name = "test_graph"
    graph.vertex_collections.return_value = ["vertices"]
    graph.edge_definitions.return_value = [
        {
            "edge_collection": "edges",
            "from_vertex_collections": ["vertices"],
            "to_vertex_collections": ["vertices"],
        }
    ]
    return graph


@pytest.fixture
def mock_view():
    """Create a mock ArangoDB view."""
    view = MagicMock()
    view.name = "test_view"
    view.properties.return_value = {
        "name": "test_view",
        "type": "arangosearch",
        "links": {},
    }
    return view


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return {
        "_key": "test_1",
        "_id": "test_collection/test_1",
        "name": "Test Document",
        "value": 42,
        "active": True,
    }


@pytest.fixture
def sample_edge():
    """Create a sample edge document for testing."""
    return {
        "_key": "edge_1",
        "_id": "edges/edge_1",
        "_from": "vertices/v1",
        "_to": "vertices/v2",
        "relationship": "related",
    }


@pytest.fixture
def sample_documents(sample_document):
    """Create multiple sample documents for batch testing."""
    return [
        sample_document,
        {**sample_document, "_key": "test_2", "value": 43},
        {**sample_document, "_key": "test_3", "value": 44},
    ]


@pytest.fixture
def arango_config():
    """
    Create test configuration for ArangoDB.

    Loads from .env file if present, otherwise uses defaults.
    Set ARANGO_HOST, ARANGO_PORT, ARANGO_USERNAME, ARANGO_PASSWORD, ARANGO_DATABASE
    """
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    return {
        "host": os.getenv("ARANGO_HOST", "localhost"),
        "port": int(os.getenv("ARANGO_PORT", "8529")),
        "username": os.getenv("ARANGO_USERNAME", "root"),
        "password": os.getenv("ARANGO_PASSWORD", ""),
        "database": os.getenv("ARANGO_DATABASE", "_system"),
    }


class TestDataFactory:
    """Factory for creating test data."""

    @staticmethod
    def create_document(key: str, **kwargs) -> Dict[str, Any]:
        """Create a document with given key and attributes."""
        doc = {"_key": key, "name": f"Document {key}", "created_at": "2024-01-01"}
        doc.update(kwargs)
        return doc

    @staticmethod
    def create_documents(count: int, prefix: str = "doc") -> list:
        """Create multiple documents."""
        return [
            TestDataFactory.create_document(f"{prefix}_{i}", index=i)
            for i in range(count)
        ]

    @staticmethod
    def create_edge(from_key: str, to_key: str, **kwargs) -> Dict[str, Any]:
        """Create an edge document."""
        edge = {
            "_key": f"{from_key}_to_{to_key}",
            "_from": f"vertices/{from_key}",
            "_to": f"vertices/{to_key}",
            "relationship": "default",
        }
        edge.update(kwargs)
        return edge

    @staticmethod
    def create_query_result(count: int, **fields) -> list:
        """Create a query result set."""
        result = []
        for i in range(count):
            row = {"_key": f"result_{i}", "index": i}
            row.update(fields)
            result.append(row)
        return result


@pytest.fixture
def data_factory():
    """Provide test data factory."""
    return TestDataFactory()
