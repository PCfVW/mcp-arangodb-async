"""Unit tests for MCP handler functions."""

import pytest
from unittest.mock import Mock, MagicMock
from mcp_arangodb.handlers import (
    handle_arango_query,
    handle_list_collections,
    handle_insert,
    handle_update,
    handle_remove,
    handle_create_collection,
    handle_backup,
    handle_explain_query,
    handle_validate_references,
    handle_insert_with_validation,
    handle_bulk_insert,
    handle_bulk_update,
)


class TestHandlers:
    """Test all handler functions with mocked database."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_collection = Mock()
        self.mock_db.collection.return_value = self.mock_collection

    def test_handle_arango_query(self):
        """Test AQL query execution."""
        # Setup
        mock_cursor = [{"name": "test1"}, {"name": "test2"}]
        self.mock_db.aql.execute.return_value = mock_cursor
        
        args = {
            "query": "FOR doc IN test RETURN doc",
            "bind_vars": {"limit": 10}
        }
        
        # Execute
        result = handle_arango_query(self.mock_db, args)
        
        # Assert
        assert result == [{"name": "test1"}, {"name": "test2"}]
        self.mock_db.aql.execute.assert_called_once_with(
            "FOR doc IN test RETURN doc", 
            bind_vars={"limit": 10}
        )

    def test_handle_explain_query(self):
        """Test explain query handler returns plans and suggestions."""
        self.mock_db.aql.explain.return_value = {
            "plans": [{"nodes": [{"type": "EnumerateCollection", "id": 1}]}],
            "warnings": [],
            "stats": {"plansCreated": 1},
        }
        args = {"query": "RETURN 1", "suggest_indexes": True, "max_plans": 1}
        result = handle_explain_query(self.mock_db, args)
        assert "plans" in result
        assert "index_suggestions" in result
        self.mock_db.aql.explain.assert_called_once()

    def test_handle_validate_references(self):
        """Test reference validation returns structure."""
        # Setup collection.count and aql.execute
        self.mock_collection.count.return_value = 2
        self.mock_db.collection.return_value = self.mock_collection
        self.mock_db.aql.execute.return_value = iter([
            {"_id": "orders/1", "_key": "1", "invalid_references": [{"field": "user_id", "value": "users/999"}]}
        ])
        args = {"collection": "orders", "reference_fields": ["user_id"], "fix_invalid": False}
        result = handle_validate_references(self.mock_db, args)
        assert result["invalid_count"] == 1
        assert result["validation_passed"] is False

    def test_handle_insert_with_validation_invalid(self):
        """Test insert with invalid references returns error payload."""
        # aql.execute returns list with invalid entries
        self.mock_db.aql.execute.return_value = iter([[{"field": "user_id", "value": "users/999"}]])
        args = {
            "collection": "orders",
            "document": {"_key": "1", "user_id": "users/999"},
            "reference_fields": ["user_id"],
        }
        result = handle_insert_with_validation(self.mock_db, args)
        assert "error" in result

    def test_handle_insert_with_validation_valid(self):
        """Test insert proceeds when validation passes."""
        # aql returns empty invalid list
        self.mock_db.aql.execute.return_value = iter([[]])
        self.mock_collection.insert.return_value = {"_id": "orders/1", "_key": "1", "_rev": "_r1"}
        self.mock_db.collection.return_value = self.mock_collection
        args = {
            "collection": "orders",
            "document": {"_key": "1", "user_id": "users/1"},
            "reference_fields": ["user_id"],
        }
        result = handle_insert_with_validation(self.mock_db, args)
        assert result["_id"] == "orders/1"

    def test_handle_bulk_insert_success(self):
        """Test bulk insert with batching success path."""
        self.mock_db.collection.return_value = self.mock_collection
        self.mock_collection.insert_many.return_value = [{"_id": "users/1"}, {"_id": "users/2"}]
        docs = [{"_key": "1"}, {"_key": "2"}]
        args = {"collection": "users", "documents": docs, "batch_size": 2}
        result = handle_bulk_insert(self.mock_db, args)
        assert result["inserted_count"] == 2
        assert result["error_count"] == 0

    def test_handle_bulk_update_success(self):
        """Test bulk update with batching success path."""
        self.mock_db.collection.return_value = self.mock_collection
        self.mock_collection.update_many.return_value = [{"_key": "1"}, {"_key": "2"}]
        updates = [{"key": "1", "update": {"age": 31}}, {"key": "2", "update": {"age": 32}}]
        args = {"collection": "users", "updates": updates, "batch_size": 2}
        result = handle_bulk_update(self.mock_db, args)
        assert result["updated_count"] == 2

    def test_handle_arango_query_no_bind_vars(self):
        """Test AQL query without bind variables."""
        mock_cursor = [{"count": 5}]
        self.mock_db.aql.execute.return_value = mock_cursor
        
        args = {"query": "RETURN LENGTH(test)"}
        
        result = handle_arango_query(self.mock_db, args)
        
        assert result == [{"count": 5}]
        self.mock_db.aql.execute.assert_called_once_with("RETURN LENGTH(test)", bind_vars={})

    def test_handle_list_collections(self):
        """Test listing collections."""
        # Setup
        mock_collections = [
            {"name": "users", "isSystem": False},
            {"name": "_graphs", "isSystem": True},
            {"name": "products", "isSystem": False},
        ]
        self.mock_db.collections.return_value = mock_collections
        
        # Execute
        result = handle_list_collections(self.mock_db)
        
        # Assert
        assert result == ["users", "products"]
        self.mock_db.collections.assert_called_once()

    def test_handle_insert(self):
        """Test document insertion."""
        # Setup
        self.mock_collection.insert.return_value = {
            "_id": "users/123",
            "_key": "123", 
            "_rev": "_abc123"
        }
        
        args = {
            "collection": "users",
            "document": {"name": "John", "age": 30}
        }
        
        # Execute
        result = handle_insert(self.mock_db, args)
        
        # Assert
        assert result == {"_id": "users/123", "_key": "123", "_rev": "_abc123"}
        self.mock_db.collection.assert_called_once_with("users")
        self.mock_collection.insert.assert_called_once_with({"name": "John", "age": 30})

    def test_handle_update(self):
        """Test document update."""
        # Setup
        self.mock_collection.update.return_value = {
            "_id": "users/123",
            "_key": "123",
            "_rev": "_def456"
        }
        
        args = {
            "collection": "users",
            "key": "123",
            "update": {"age": 31}
        }
        
        # Execute
        result = handle_update(self.mock_db, args)
        
        # Assert
        assert result == {"_id": "users/123", "_key": "123", "_rev": "_def456"}
        self.mock_db.collection.assert_called_once_with("users")
        self.mock_collection.update.assert_called_once_with({"_key": "123", "age": 31})

    def test_handle_remove(self):
        """Test document removal."""
        # Setup
        self.mock_collection.delete.return_value = {
            "_id": "users/123",
            "_key": "123",
            "_rev": "_ghi789"
        }
        
        args = {
            "collection": "users",
            "key": "123"
        }
        
        # Execute
        result = handle_remove(self.mock_db, args)
        
        # Assert
        assert result == {"_id": "users/123", "_key": "123", "_rev": "_ghi789"}
        self.mock_db.collection.assert_called_once_with("users")
        self.mock_collection.delete.assert_called_once_with("123")

    def test_handle_create_collection_new_document(self):
        """Test creating new document collection."""
        # Setup
        self.mock_db.has_collection.return_value = False
        mock_new_collection = Mock()
        mock_new_collection.properties.return_value = {
            "name": "test_collection",
            "type": 2,  # document collection
            "waitForSync": False
        }
        self.mock_db.create_collection.return_value = mock_new_collection
        
        args = {
            "name": "test_collection",
            "type": "document",
            "waitForSync": False
        }
        
        # Execute
        result = handle_create_collection(self.mock_db, args)
        
        # Assert
        assert result == {
            "name": "test_collection",
            "type": "document",
            "waitForSync": False
        }
        self.mock_db.has_collection.assert_called_once_with("test_collection")
        self.mock_db.create_collection.assert_called_once_with("test_collection", edge=False, sync=False)

    def test_handle_create_collection_existing(self):
        """Test getting existing collection."""
        # Setup
        self.mock_db.has_collection.return_value = True
        self.mock_collection.properties.return_value = {
            "name": "existing_collection",
            "type": 3,  # edge collection
            "waitForSync": True
        }
        
        args = {"name": "existing_collection"}
        
        # Execute
        result = handle_create_collection(self.mock_db, args)
        
        # Assert
        assert result == {
            "name": "existing_collection",
            "type": "edge",
            "waitForSync": True
        }
        self.mock_db.has_collection.assert_called_once_with("existing_collection")
        self.mock_db.collection.assert_called_once_with("existing_collection")

    @pytest.fixture
    def mock_backup_function(self, monkeypatch):
        """Mock the backup function."""
        mock_backup = Mock()
        mock_backup.return_value = {
            "output_dir": "/tmp/backup",
            "written": [{"collection": "users", "path": "/tmp/backup/users.json", "count": 10}],
            "total_collections": 1,
            "total_documents": 10
        }
        monkeypatch.setattr("mcp_arangodb.handlers.backup_collections_to_dir", mock_backup)
        return mock_backup

    def test_handle_backup_single_collection(self, mock_backup_function):
        """Test backup with single collection."""
        args = {
            "collection": "users",
            "output_dir": "/tmp/backup"
        }
        
        result = handle_backup(self.mock_db, args)
        
        assert result["total_collections"] == 1
        assert result["total_documents"] == 10
        mock_backup_function.assert_called_once_with(
            self.mock_db,
            output_dir="/tmp/backup",
            collections=["users"],
            doc_limit=None
        )

    def test_handle_backup_multiple_collections(self, mock_backup_function):
        """Test backup with multiple collections."""
        args = {
            "collections": ["users", "products"],
            "outputDir": "/tmp/backup",
            "docLimit": 100
        }
        
        result = handle_backup(self.mock_db, args)
        
        assert result["total_collections"] == 1
        mock_backup_function.assert_called_once_with(
            self.mock_db,
            output_dir="/tmp/backup",
            collections=["users", "products"],
            doc_limit=100
        )
