"""Unit tests for MCP handler functions."""

import pytest
from unittest.mock import Mock, MagicMock
from mcp_arangodb_async.handlers import (
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
    # New graph management handlers
    handle_backup_graph,
    handle_restore_graph,
    handle_backup_named_graphs,
    handle_validate_graph_integrity,
    handle_graph_statistics,
    handle_bulk_insert,
    handle_bulk_update,
    # MCP Design Pattern handlers
    handle_search_tools,
    handle_list_tools_by_category,
    handle_switch_context,
    handle_get_active_context,
    handle_list_contexts,
    handle_advance_workflow_stage,
    handle_get_tool_usage_stats,
    handle_unload_tools,
    TOOL_CATEGORIES,
    WORKFLOW_CONTEXTS,
    WORKFLOW_STAGES,
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
        monkeypatch.setattr("mcp_arangodb_async.handlers.backup_collections_to_dir", mock_backup)
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


class TestGraphManagementHandlers:
    """Test cases for new graph management handler functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()

    @pytest.fixture
    def mock_backup_graph_function(self, monkeypatch):
        """Mock the backup_graph_to_dir function."""
        mock_backup = Mock()
        mock_backup.return_value = {
            "graph_name": "test_graph",
            "output_dir": "/tmp/graph_backup",
            "vertex_files": [{"collection": "users", "count": 10}],
            "edge_files": [{"collection": "follows", "count": 5}],
            "total_vertex_collections": 1,
            "total_edge_collections": 1,
            "total_documents": 15,
            "metadata_included": True
        }
        monkeypatch.setattr("mcp_arangodb_async.handlers.backup_graph_to_dir", mock_backup)
        return mock_backup

    def test_handle_backup_graph_success(self, mock_backup_graph_function):
        """Test successful graph backup."""
        args = {
            "graph_name": "test_graph",
            "output_dir": "/tmp/graph_backup",
            "include_metadata": True,
            "doc_limit": 1000
        }

        result = handle_backup_graph(self.mock_db, args)

        assert result["graph_name"] == "test_graph"
        assert result["total_documents"] == 15
        mock_backup_graph_function.assert_called_once_with(
            self.mock_db,
            "test_graph",
            "/tmp/graph_backup",
            True,
            1000
        )

    def test_handle_backup_graph_minimal_args(self, mock_backup_graph_function):
        """Test graph backup with minimal arguments."""
        args = {"graph_name": "minimal_graph"}

        result = handle_backup_graph(self.mock_db, args)

        assert result["graph_name"] == "test_graph"
        mock_backup_graph_function.assert_called_once_with(
            self.mock_db,
            "minimal_graph",
            None,  # output_dir default
            True,  # include_metadata default
            None   # doc_limit default
        )

    @pytest.fixture
    def mock_restore_graph_function(self, monkeypatch):
        """Mock the restore_graph_from_dir function."""
        mock_restore = Mock()
        mock_restore.return_value = {
            "graph_name": "restored_graph",
            "original_graph_name": "test_graph",
            "input_dir": "/tmp/backup",
            "restored_vertices": [{"collection": "users", "inserted": 10}],
            "restored_edges": [{"collection": "follows", "inserted": 5}],
            "graph_created": True,
            "conflicts": [],
            "errors": [],
            "integrity_report": {"valid": True},
            "total_documents_restored": 15
        }
        monkeypatch.setattr("mcp_arangodb_async.handlers.restore_graph_from_dir", mock_restore)
        return mock_restore

    def test_handle_restore_graph_success(self, mock_restore_graph_function):
        """Test successful graph restore."""
        args = {
            "input_dir": "/tmp/backup",
            "graph_name": "restored_graph",
            "conflict_resolution": "overwrite",
            "validate_integrity": True
        }

        result = handle_restore_graph(self.mock_db, args)

        assert result["graph_name"] == "restored_graph"
        assert result["graph_created"] is True
        assert result["total_documents_restored"] == 15
        mock_restore_graph_function.assert_called_once_with(
            self.mock_db,
            "/tmp/backup",
            "restored_graph",
            "overwrite",
            True
        )

    def test_handle_restore_graph_minimal_args(self, mock_restore_graph_function):
        """Test graph restore with minimal arguments."""
        args = {"input_dir": "/tmp/backup"}

        result = handle_restore_graph(self.mock_db, args)

        assert result["graph_name"] == "restored_graph"
        mock_restore_graph_function.assert_called_once_with(
            self.mock_db,
            "/tmp/backup",
            None,    # graph_name default
            "error", # conflict_resolution default
            True     # validate_integrity default
        )

    @pytest.fixture
    def mock_backup_named_graphs_function(self, monkeypatch):
        """Mock the backup_named_graphs function."""
        mock_backup = Mock()
        mock_backup.return_value = {
            "output_file": "/tmp/graphs.json",
            "graphs_backed_up": 2,
            "missing_graphs": [],
            "backup_size_bytes": 1024
        }
        monkeypatch.setattr("mcp_arangodb_async.handlers.backup_named_graphs", mock_backup)
        return mock_backup

    def test_handle_backup_named_graphs_success(self, mock_backup_named_graphs_function):
        """Test successful named graphs backup."""
        args = {
            "output_file": "/tmp/graphs.json",
            "graph_names": ["graph1", "graph2"]
        }

        result = handle_backup_named_graphs(self.mock_db, args)

        assert result["graphs_backed_up"] == 2
        assert result["missing_graphs"] == []
        mock_backup_named_graphs_function.assert_called_once_with(
            self.mock_db,
            "/tmp/graphs.json",
            ["graph1", "graph2"]
        )

    def test_handle_backup_named_graphs_minimal_args(self, mock_backup_named_graphs_function):
        """Test named graphs backup with minimal arguments."""
        args = {}

        result = handle_backup_named_graphs(self.mock_db, args)

        assert result["graphs_backed_up"] == 2
        mock_backup_named_graphs_function.assert_called_once_with(
            self.mock_db,
            None,  # output_file default
            None   # graph_names default
        )

    @pytest.fixture
    def mock_validate_graph_integrity_function(self, monkeypatch):
        """Mock the validate_graph_integrity function."""
        mock_validate = Mock()
        mock_validate.return_value = {
            "valid": True,
            "graphs_checked": 1,
            "total_orphaned_edges": 0,
            "total_constraint_violations": 0,
            "results": [{
                "graph_name": "test_graph",
                "valid": True,
                "orphaned_edges_count": 0,
                "constraint_violations_count": 0,
                "orphaned_edges": [],
                "constraint_violations": []
            }],
            "summary": "Checked 1 graphs: 0 orphaned edges, 0 violations"
        }
        monkeypatch.setattr("mcp_arangodb_async.handlers.validate_graph_integrity", mock_validate)
        return mock_validate

    def test_handle_validate_graph_integrity_success(self, mock_validate_graph_integrity_function):
        """Test successful graph integrity validation."""
        args = {
            "graph_name": "test_graph",
            "check_orphaned_edges": True,
            "check_constraints": True,
            "return_details": False
        }

        result = handle_validate_graph_integrity(self.mock_db, args)

        assert result["valid"] is True
        assert result["graphs_checked"] == 1
        assert result["total_orphaned_edges"] == 0
        mock_validate_graph_integrity_function.assert_called_once_with(
            self.mock_db,
            "test_graph",
            True,
            True,
            False
        )

    def test_handle_validate_graph_integrity_minimal_args(self, mock_validate_graph_integrity_function):
        """Test graph integrity validation with minimal arguments."""
        args = {}

        result = handle_validate_graph_integrity(self.mock_db, args)

        assert result["valid"] is True
        mock_validate_graph_integrity_function.assert_called_once_with(
            self.mock_db,
            None,  # graph_name default
            True,  # check_orphaned_edges default
            True,  # check_constraints default
            False  # return_details default
        )

    @pytest.fixture
    def mock_calculate_graph_statistics_function(self, monkeypatch):
        """Mock the calculate_graph_statistics function."""
        mock_stats = Mock()
        mock_stats.return_value = {
            "graphs_analyzed": 1,
            "statistics": [{
                "graph_name": "test_graph",
                "vertex_collections": ["users"],
                "edge_collections": ["follows"],
                "total_vertices": 100,
                "total_edges": 50,
                "density": 0.01,
                "out_degree_distribution": [{"degree": 1, "frequency": 80}],
                "max_out_degree": 5,
                "avg_out_degree": 0.5,
                "connectivity_sample_size": 10,
                "avg_reachable_vertices": 25.5,
                "max_reachable_vertices": 50
            }],
            "analysis_timestamp": "2024-01-01T12:00:00"
        }
        monkeypatch.setattr("mcp_arangodb_async.handlers.calculate_graph_statistics", mock_stats)
        return mock_stats

    def test_handle_graph_statistics_success(self, mock_calculate_graph_statistics_function):
        """Test successful graph statistics calculation."""
        args = {
            "graph_name": "test_graph",
            "include_degree_distribution": True,
            "include_connectivity": True,
            "sample_size": 100
        }

        result = handle_graph_statistics(self.mock_db, args)

        assert result["graphs_analyzed"] == 1
        assert len(result["statistics"]) == 1
        assert result["statistics"][0]["total_vertices"] == 100
        assert result["statistics"][0]["total_edges"] == 50
        mock_calculate_graph_statistics_function.assert_called_once_with(
            self.mock_db,
            "test_graph",
            True,
            True,
            100,
            False,  # aggregate_collections
            False   # per_collection_stats
        )

    def test_handle_graph_statistics_minimal_args(self, mock_calculate_graph_statistics_function):
        """Test graph statistics calculation with minimal arguments."""
        args = {}

        result = handle_graph_statistics(self.mock_db, args)

        assert result["graphs_analyzed"] == 1
        mock_calculate_graph_statistics_function.assert_called_once_with(
            self.mock_db,
            None,  # graph_name default
            True,  # include_degree_distribution default
            True,  # include_connectivity default
            None,  # sample_size default
            False, # aggregate_collections default
            False  # per_collection_stats default
        )


class TestMCPDesignPatternHandlers:
    """Test MCP Design Pattern tool handlers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()

    # ========================================================================
    # Pattern 1: Progressive Tool Discovery
    # ========================================================================

    def test_handle_search_tools_by_keywords(self):
        """Test searching tools by keywords returns matching tools."""
        args = {
            "keywords": ["query", "graph"],
            "categories": None,
            "detail_level": "summary"
        }

        result = handle_search_tools(self.mock_db, args)

        assert "matches" in result
        assert "total_matches" in result
        assert "keywords" in result
        assert result["keywords"] == ["query", "graph"]
        assert result["detail_level"] == "summary"
        assert isinstance(result["matches"], list)
        # Should find tools with "query" or "graph" in name/description
        assert result["total_matches"] > 0

    def test_handle_search_tools_with_category_filter(self):
        """Test searching tools with category filter."""
        args = {
            "keywords": ["insert"],
            "categories": ["core_data"],
            "detail_level": "name"
        }

        result = handle_search_tools(self.mock_db, args)

        assert result["categories_searched"] == ["core_data"]
        assert result["detail_level"] == "name"
        # All matches should only have "name" field
        for match in result["matches"]:
            assert "name" in match
            assert "description" not in match or len(match) == 1

    def test_handle_search_tools_full_detail(self):
        """Test searching tools with full detail level includes schemas."""
        args = {
            "keywords": ["query"],
            "categories": None,
            "detail_level": "full"
        }

        result = handle_search_tools(self.mock_db, args)

        assert result["detail_level"] == "full"
        # At least one match should have inputSchema
        if result["total_matches"] > 0:
            first_match = result["matches"][0]
            assert "name" in first_match
            assert "description" in first_match
            assert "inputSchema" in first_match

    def test_handle_list_tools_by_category_all(self):
        """Test listing all tool categories."""
        args = {"category": None}

        result = handle_list_tools_by_category(self.mock_db, args)

        assert "categories" in result
        assert "total_tools" in result
        assert len(result["categories"]) == 9  # 9 categories defined
        assert "core_data" in result["categories"]
        assert "graph_basic" in result["categories"]
        assert result["total_tools"] > 0

    def test_handle_list_tools_by_category_single(self):
        """Test listing tools for a single category."""
        args = {"category": "core_data"}

        result = handle_list_tools_by_category(self.mock_db, args)

        assert result["category"] == "core_data"
        assert "tools" in result
        assert "tool_count" in result
        assert isinstance(result["tools"], list)
        assert result["tool_count"] == len(result["tools"])
        # Verify core_data tools are present
        assert result["tool_count"] > 0

    def test_handle_list_tools_by_category_invalid(self):
        """Test listing tools with invalid category returns error."""
        args = {"category": "invalid_category"}

        result = handle_list_tools_by_category(self.mock_db, args)

        assert "error" in result
        assert "available_categories" in result
        assert "invalid_category" in result["error"]

    # ========================================================================
    # Pattern 2: Context Switching
    # ========================================================================

    def test_handle_switch_context_valid(self):
        """Test switching to a valid workflow context."""
        args = {"context": "graph_modeling"}

        result = handle_switch_context(self.mock_db, args)

        assert "from_context" in result
        assert "to_context" in result
        assert result["to_context"] == "graph_modeling"
        assert "description" in result
        assert "tools_added" in result
        assert "tools_removed" in result
        assert "total_tools" in result
        assert "active_tools" in result
        assert isinstance(result["active_tools"], list)

    def test_handle_switch_context_invalid(self):
        """Test switching to invalid context returns error."""
        args = {"context": "invalid_context"}

        result = handle_switch_context(self.mock_db, args)

        assert "error" in result
        assert "available_contexts" in result
        assert "invalid_context" in result["error"]

    def test_handle_switch_context_tracks_changes(self):
        """Test context switching tracks tool additions and removals."""
        # First switch to data_analysis
        args1 = {"context": "data_analysis"}
        result1 = handle_switch_context(self.mock_db, args1)

        # Then switch to graph_modeling
        args2 = {"context": "graph_modeling"}
        result2 = handle_switch_context(self.mock_db, args2)

        assert result2["from_context"] == "data_analysis"
        assert result2["to_context"] == "graph_modeling"
        # Should have tools added and removed
        assert isinstance(result2["tools_added"], list)
        assert isinstance(result2["tools_removed"], list)

    def test_handle_get_active_context(self):
        """Test getting the currently active context."""
        # Switch to a known context first
        switch_args = {"context": "bulk_operations"}
        handle_switch_context(self.mock_db, switch_args)

        # Now get active context
        result = handle_get_active_context(self.mock_db, None)

        assert "active_context" in result
        assert result["active_context"] == "bulk_operations"
        assert "description" in result
        assert "tools" in result
        assert "tool_count" in result
        assert isinstance(result["tools"], list)
        assert result["tool_count"] == len(result["tools"])

    def test_handle_list_contexts_without_tools(self):
        """Test listing all contexts without tool details."""
        args = {"include_tools": False}

        result = handle_list_contexts(self.mock_db, args)

        assert "contexts" in result
        assert "total_contexts" in result
        assert "active_context" in result
        assert len(result["contexts"]) == 6  # 6 workflow contexts

        # Verify each context has description and tool_count but not tools
        for context_name, context_info in result["contexts"].items():
            assert "description" in context_info
            assert "tool_count" in context_info
            assert "tools" not in context_info

    def test_handle_list_contexts_with_tools(self):
        """Test listing all contexts with tool details."""
        args = {"include_tools": True}

        result = handle_list_contexts(self.mock_db, args)

        assert "contexts" in result
        assert len(result["contexts"]) == 6

        # Verify each context includes tools list
        for context_name, context_info in result["contexts"].items():
            assert "description" in context_info
            assert "tool_count" in context_info
            assert "tools" in context_info
            assert isinstance(context_info["tools"], list)

    # ========================================================================
    # Pattern 3: Tool Unloading
    # ========================================================================

    def test_handle_advance_workflow_stage_valid(self):
        """Test advancing to a valid workflow stage."""
        args = {"stage": "data_loading"}

        result = handle_advance_workflow_stage(self.mock_db, args)

        assert "from_stage" in result
        assert "to_stage" in result
        assert result["to_stage"] == "data_loading"
        assert "description" in result
        assert "tools_unloaded" in result
        assert "tools_loaded" in result
        assert "active_tools" in result
        assert "total_active_tools" in result
        assert isinstance(result["active_tools"], list)
        assert result["total_active_tools"] == len(result["active_tools"])

    def test_handle_advance_workflow_stage_invalid(self):
        """Test advancing to invalid stage returns error."""
        args = {"stage": "invalid_stage"}

        result = handle_advance_workflow_stage(self.mock_db, args)

        assert "error" in result
        assert "available_stages" in result
        assert "invalid_stage" in result["error"]

    def test_handle_advance_workflow_stage_progression(self):
        """Test stage progression tracks tool lifecycle."""
        # First, reset to setup stage
        reset_args = {"stage": "setup"}
        handle_advance_workflow_stage(self.mock_db, reset_args)

        # Advance from setup to data_loading
        args1 = {"stage": "data_loading"}
        result1 = handle_advance_workflow_stage(self.mock_db, args1)

        assert result1["from_stage"] == "setup"
        assert result1["to_stage"] == "data_loading"

        # Advance to analysis
        args2 = {"stage": "analysis"}
        result2 = handle_advance_workflow_stage(self.mock_db, args2)

        assert result2["from_stage"] == "data_loading"
        assert result2["to_stage"] == "analysis"
        assert isinstance(result2["tools_unloaded"], list)
        assert isinstance(result2["tools_loaded"], list)

    def test_handle_get_tool_usage_stats(self):
        """Test getting tool usage statistics."""
        result = handle_get_tool_usage_stats(self.mock_db, None)

        assert "current_stage" in result
        assert "tool_usage" in result
        assert "total_tools_used" in result
        assert "active_stage_tools" in result
        assert isinstance(result["tool_usage"], dict)
        assert isinstance(result["active_stage_tools"], list)

    def test_handle_unload_tools_valid(self):
        """Test manually unloading valid tools."""
        from mcp_arangodb_async.tools import ARANGO_QUERY, ARANGO_INSERT

        args = {"tool_names": [ARANGO_QUERY, ARANGO_INSERT]}

        result = handle_unload_tools(self.mock_db, args)

        assert "unloaded" in result
        assert "not_found" in result
        assert "total_unloaded" in result
        assert ARANGO_QUERY in result["unloaded"]
        assert ARANGO_INSERT in result["unloaded"]
        assert result["total_unloaded"] == 2

    def test_handle_unload_tools_invalid(self):
        """Test unloading invalid tools tracks not found."""
        args = {"tool_names": ["invalid_tool_1", "invalid_tool_2"]}

        result = handle_unload_tools(self.mock_db, args)

        assert "unloaded" in result
        assert "not_found" in result
        assert len(result["not_found"]) == 2
        assert "invalid_tool_1" in result["not_found"]
        assert "invalid_tool_2" in result["not_found"]
        assert result["total_unloaded"] == 0

    def test_handle_unload_tools_mixed(self):
        """Test unloading mix of valid and invalid tools."""
        from mcp_arangodb_async.tools import ARANGO_QUERY

        args = {"tool_names": [ARANGO_QUERY, "invalid_tool"]}

        result = handle_unload_tools(self.mock_db, args)

        assert ARANGO_QUERY in result["unloaded"]
        assert "invalid_tool" in result["not_found"]
        assert result["total_unloaded"] == 1
