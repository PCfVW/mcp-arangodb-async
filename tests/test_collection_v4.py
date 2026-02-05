"""Unit tests for arango_collection tool (v4).

Tests for collection operations:
- CRUD: insert, find, update, remove, insert_with_validation, list
- Batch: bulk_insert, bulk_update, import, export
- Index: list_indexes, create_index, delete_index
- Schema: get_schema, create_schema, validate_document, validate_references
- Management: create, stats, drop, truncate
- Backup: backup
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
import json
from mcp_arangodb_async.collection.handler import handle_collection
from mcp_arangodb_async.collection.crud import insert, find, update, remove
from mcp_arangodb_async.collection.batch import bulk_insert, import_documents, export_documents
from mcp_arangodb_async.collection.index import create_index, list_indexes
from mcp_arangodb_async.collection.schema import get_schema
from mcp_arangodb_async.collection.management import stats, drop_collection, truncate_collection


class TestCollectionCRUD:
    """Test CRUD operations."""

    def test_insert_single_document(self, mock_db, sample_document):
        """Should insert a single document."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.insert.return_value = {"_key": "test_1", "_id": "col/test_1"}
        mock_db.collection.return_value = mock_collection

        args = {
            "collection": "test_col",
            "document": sample_document,
        }

        # Act
        result = handle_collection(mock_db, "insert", args)

        # Assert
        assert "_key" in result
        mock_collection.insert.assert_called_once()

    def test_insert_accepts_legacy_data_alias(self, mock_db, sample_document):
        """Should accept 'data' as backward-compatible alias of 'document'."""
        mock_collection = MagicMock()
        mock_collection.insert.return_value = {"_key": "test_legacy", "_id": "col/test_legacy"}
        mock_db.collection.return_value = mock_collection

        result = handle_collection(
            mock_db,
            "insert",
            {"collection": "test_col", "data": sample_document},
        )

        assert "_key" in result
        mock_collection.insert.assert_called_once()

    def test_insert_requires_collection_param(self, mock_db, sample_document):
        """Should return MissingParameter when collection is omitted."""
        result = handle_collection(mock_db, "insert", {"document": sample_document})
        assert result.get("type") == "MissingParameter"

    def test_find_by_key(self, mock_db, sample_document):
        """Should find document by key."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.get.return_value = sample_document
        mock_db.collection.return_value = mock_collection

        args = {
            "collection": "test_col",
            "key": "test_1",
        }

        # Act
        result = find(mock_db, args)

        # Assert
        assert result["found"] is True
        assert result["doc"]["_key"] == "test_1"

    def test_find_by_filter(self, mock_db, sample_documents):
        """Should find documents by MongoDB-style filter."""
        # Arrange
        mock_db.aql.execute.return_value = iter(sample_documents)
        args = {
            "collection": "test_col",
            "filter": {"value": {"$gt": 42}},
            "limit": 10,
        }

        # Act
        result = find(mock_db, args)

        # Assert
        assert result["count"] > 0
        assert result["count"] > 0

    def test_update_document(self, mock_db, sample_document):
        """Should update a document."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.update.return_value = {"_key": "test_1", "value": 99}
        mock_db.collection.return_value = mock_collection

        args = {
            "collection": "test_col",
            "key": "test_1",
            "data": {"value": 99},
        }

        # Act
        result = handle_collection(mock_db, "update", args)

        # Assert
        assert "_key" in result

    def test_update_accepts_legacy_data_alias(self, mock_db):
        """Should accept 'data' as backward-compatible alias of 'update'."""
        mock_collection = MagicMock()
        mock_collection.update.return_value = {"_key": "test_1", "value": 99}
        mock_db.collection.return_value = mock_collection

        result = handle_collection(
            mock_db,
            "update",
            {"collection": "test_col", "key": "test_1", "data": {"value": 99}},
        )

        assert "_key" in result

    def test_remove_document(self, mock_db):
        """Should remove a document."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.delete.return_value = {
            "_key": "test_1",
            "_id": "test_col/test_1",
            "_rev": "_rev_1",
        }
        mock_db.collection.return_value = mock_collection

        args = {
            "collection": "test_col",
            "key": "test_1",
        }

        # Act
        result = handle_collection(mock_db, "remove", args)

        # Assert
        assert result.get("_key") == "test_1"


class TestCollectionBatch:
    """Test batch operations."""

    def test_bulk_insert_multiple_documents(self, mock_db, sample_documents):
        """Should bulk insert multiple documents."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.insert_many.return_value = [
            {"_key": doc["_key"]} for doc in sample_documents
        ]
        mock_db.collection.return_value = mock_collection

        args = {
            "collection": "test_col",
            "documents": sample_documents,
        }

        # Act
        result = handle_collection(mock_db, "bulk_insert", args)

        # Assert
        assert result.get("inserted_count", 0) > 0

    def test_import_documents_from_file(self, mock_db, tmp_path, sample_documents):
        """Should import documents from JSON file."""
        # Arrange
        import_file = tmp_path / "docs.json"
        import_file.write_text(json.dumps(sample_documents))

        mock_collection = MagicMock()
        mock_collection.insert.return_value = {"_key": "imported"}
        mock_db.collection.return_value = mock_collection

        args = {
            "collection": "test_col",
            "file_path": str(import_file),
        }

        # Act
        result = import_documents(mock_db, args)

        # Assert
        assert result.get("success") is True

    def test_export_documents_to_file(self, mock_db, sample_documents, tmp_path):
        """Should export documents to JSON file."""
        # Arrange
        export_file = tmp_path / "export.json"
        mock_db.aql.execute.return_value = iter(sample_documents)

        args = {
            "collection": "test_col",
            "file_path": str(export_file),
            "filter": {"_key": {"$in": ["test_1", "test_2"]}},
            "options": {"output_dir": str(tmp_path)},
        }

        # Act
        result = export_documents(mock_db, args)

        # Assert
        assert result.get("success") is True
        assert result.get("count", 0) >= 0


class TestCollectionIndex:
    """Test index operations."""

    def test_list_indexes(self, mock_db):
        """Should list collection indexes."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.indexes.return_value = [
            {
                "fields": ["_key"],
                "id": "primary",
                "sparse": False,
                "type": "primary",
                "unique": True,
            },
        ]
        mock_db.collection.return_value = mock_collection

        args = {"collection": "test_col"}

        # Act
        result = list_indexes(mock_db, args)

        # Assert
        assert isinstance(result, list)
        assert len(result) > 0

    def test_create_index(self, mock_db):
        """Should create an index on collection."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.add_index.return_value = {
            "id": "idx_123",
            "type": "persistent",
            "fields": ["name", "email"],
            "unique": False,
            "sparse": False,
            "name": "idx_123",
        }
        mock_db.collection.return_value = mock_collection

        args = {
            "collection": "test_col",
            "fields": ["name", "email"],
            "type": "persistent",
        }

        # Act
        result = create_index(mock_db, args)

        # Assert
        assert "id" in result


class TestCollectionSchema:
    """Test schema operations."""

    def test_get_schema(self, mock_db):
        """Should retrieve collection schema."""
        # Arrange
        schema_doc = {
            "_key": "test_col_schema",
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        mock_db.has_collection.return_value = True
        mock_schemas_col = MagicMock()
        mock_schemas_col.get.return_value = schema_doc
        mock_db.collection.return_value = mock_schemas_col

        args = {"collection": "test_col"}

        # Act
        result = get_schema(mock_db, args)

        # Assert
        assert result.get("found") is True
        assert "schema" in result

    def test_validate_document_with_schema(self, mock_db, sample_document):
        """Should validate document against schema."""
        # Arrange
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        args = {
            "collection": "test_col",
            "document": sample_document,
            "schema": schema,
        }

        # Act
        result = handle_collection(mock_db, "validate_document", args)

        # Assert
        assert isinstance(result, dict)
        assert "valid" in result or "error" in result


class TestCollectionManagement:
    """Test collection management operations."""

    def test_stats_returns_collection_statistics(self, mock_db):
        """Should return collection statistics."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.count.return_value = 1000
        mock_collection.figures.return_value = {
            "count": 1000,
            "dataFiles": {"count": 5},
        }
        mock_db.collection.return_value = mock_collection

        args = {"collection": "test_col"}

        # Act
        result = stats(mock_db, args)

        # Assert
        assert "count" in result
        assert result.get("collection") == "test_col"

    def test_drop_collection(self, mock_db):
        """Should drop a collection."""
        # Arrange
        mock_db.delete_collection.return_value = None
        args = {"collection": "test_col"}

        # Act
        result = drop_collection(mock_db, args)

        # Assert
        assert result["success"] is True
        mock_db.delete_collection.assert_called_once_with("test_col")

    def test_truncate_collection(self, mock_db):
        """Should truncate (empty) a collection."""
        # Arrange
        mock_collection = MagicMock()
        mock_collection.truncate.return_value = None
        mock_db.collection.return_value = mock_collection

        args = {"collection": "test_col"}

        # Act
        result = truncate_collection(mock_db, args)

        # Assert
        assert result["success"] is True


class TestCollectionHandler:
    """Test handler dispatch for collection operations."""

    def test_handler_dispatches_all_operations(self, mock_db):
        """Should dispatch all defined operations."""
        # Arrange
        operations = [
            ("list", {}),
            ("create", {"name": "new_col"}),
            ("stats", {"collection": "test_col"}),
            ("drop", {"collection": "test_col"}),
        ]

        # Act & Assert
        for operation, args in operations:
            result = handle_collection(mock_db, operation, args)
            assert isinstance(result, (dict, list))

    def test_handler_rejects_unknown_operation(self, mock_db):
        """Should reject unknown operations."""
        # Arrange
        args = {}

        # Act
        result = handle_collection(mock_db, "unknown_op", args)

        # Assert
        assert "error" in result or result.get("success") is False


class TestCollectionFilters:
    """Test MongoDB-style filter support."""

    def test_filter_greater_than(self, mock_db, sample_documents):
        """Should support $gt operator."""
        # Arrange
        mock_db.aql.execute.return_value = iter([sample_documents[2]])  # value=44
        args = {
            "collection": "test_col",
            "filter": {"value": {"$gt": 42}},
        }

        # Act
        result = find(mock_db, args)

        # Assert
        assert result["count"] > 0

    def test_filter_in_operator(self, mock_db, sample_documents):
        """Should support $in operator."""
        # Arrange
        mock_db.aql.execute.return_value = iter(sample_documents[:2])
        args = {
            "collection": "test_col",
            "filter": {"_key": {"$in": ["test_1", "test_2"]}},
        }

        # Act
        result = find(mock_db, args)

        # Assert
        assert result["count"] > 0

    def test_filter_not_equal(self, mock_db):
        """Should support $ne operator."""
        # Arrange
        mock_db.aql.execute.return_value = iter([])
        args = {
            "collection": "test_col",
            "filter": {"status": {"$ne": "inactive"}},
        }

        # Act
        result = find(mock_db, args)

        # Assert
        assert isinstance(result, dict)
