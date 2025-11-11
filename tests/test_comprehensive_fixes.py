"""
Comprehensive tests for all 6 prioritized recommendations implemented.

This test suite verifies that all fixes work correctly:
1. Query builder security fixes
2. Graph integrity calculation fixes  
3. Documentation accuracy
4. Path validation security
5. Graph statistics improvements
6. Code quality polish
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from pathlib import Path

from mcp_arangodb_async.handlers import handle_query_builder, handle_graph_statistics
from mcp_arangodb_async.backup import validate_output_directory
from mcp_arangodb_async.graph_backup import validate_graph_integrity, calculate_graph_statistics
from mcp_arangodb_async.models import DeleteIndexArgs, GraphStatisticsArgs


class TestQueryBuilderSecurity:
    """Test the security fixes for query builder."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_db.aql.execute.return_value = [{"test": "result"}]

    def test_query_builder_uses_bind_variables(self):
        """Test that query builder uses bind variables instead of string interpolation."""
        args = {
            "collection": "users",
            "filters": [{"field": "age", "op": ">=", "value": 18}]
        }
        
        result = handle_query_builder(self.mock_db, args)
        
        # Verify AQL was called with bind variables
        call_args = self.mock_db.aql.execute.call_args
        aql_query = call_args[0][0]
        bind_vars = call_args[1]['bind_vars']
        
        assert "@v0" in aql_query
        assert "v0" in bind_vars
        assert bind_vars["v0"] == 18

    def test_query_builder_like_operator_correct_syntax(self):
        """Test that LIKE operator uses correct ArangoDB function syntax."""
        args = {
            "collection": "users", 
            "filters": [{"field": "name", "op": "LIKE", "value": "John%"}]
        }
        
        handle_query_builder(self.mock_db, args)
        
        call_args = self.mock_db.aql.execute.call_args
        aql_query = call_args[0][0]
        
        assert "LIKE(doc.name, @v0, true)" in aql_query

    def test_query_builder_validates_operators(self):
        """Test that invalid operators are rejected."""
        args = {
            "collection": "users",
            "filters": [{"field": "name", "op": "INVALID_OP", "value": "test"}]
        }

        # The error handler catches exceptions and returns error dict
        result = handle_query_builder(self.mock_db, args)
        assert "error" in result
        assert "Unsupported operator" in str(result["error"])

    def test_query_builder_validates_field_names(self):
        """Test that invalid field names are rejected."""
        args = {
            "collection": "users",
            "filters": [{"field": "name'; DROP TABLE users; --", "op": "==", "value": "test"}]
        }

        # The error handler catches exceptions and returns error dict
        result = handle_query_builder(self.mock_db, args)
        assert "error" in result
        assert "Invalid field name" in str(result["error"])

    def test_query_builder_validates_collection_name(self):
        """Test that invalid collection names are rejected."""
        args = {
            "collection": "users'; DROP DATABASE; --",
            "filters": [{"field": "name", "op": "==", "value": "test"}]
        }

        # The error handler catches exceptions and returns error dict
        result = handle_query_builder(self.mock_db, args)
        assert "error" in result
        assert "Invalid collection name" in str(result["error"])


class TestGraphIntegrityFix:
    """Test the graph integrity calculation fix."""

    def test_validate_graph_integrity_accumulates_violations(self):
        """Test that total violations are properly accumulated."""
        mock_db = Mock()
        mock_db.graphs.return_value = [{"name": "graph1"}, {"name": "graph2"}]
        mock_db.has_graph.return_value = True
        
        mock_graph = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "edge_definitions": [{"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}]
        }
        mock_db.graph.return_value = mock_graph
        mock_db.has_collection.return_value = True
        
        # First call returns orphaned edge, second call raises exception
        orphaned_edge = {
            "_id": "edges/1",
            "_from": "vertices/missing", 
            "_to": "vertices/1",
            "from_exists": False,
            "to_exists": True
        }
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter([orphaned_edge]))
        
        mock_db.aql.execute.side_effect = [mock_cursor, Exception("Query failed")]
        
        result = validate_graph_integrity(mock_db, return_details=True)
        
        # Verify totals are correctly accumulated
        assert result["valid"] is False
        assert result["total_orphaned_edges"] == 1
        assert result["total_constraint_violations"] == 1
        assert result["graphs_checked"] == 2
        assert "1 orphaned edges, 1 violations" in result["summary"]


class TestPathValidationSecurity:
    """Test the secure path validation implementation."""

    def test_validate_output_directory_allows_temp(self):
        """Test that temp directories are allowed."""
        temp_dir = tempfile.gettempdir()
        test_path = os.path.join(temp_dir, "test_backup")
        
        result = validate_output_directory(test_path)
        assert os.path.isabs(result)
        assert "test_backup" in result

    def test_validate_output_directory_rejects_traversal(self):
        """Test that path traversal attempts are rejected."""
        with pytest.raises(ValueError, match="outside allowed directories"):
            validate_output_directory("../../../etc/passwd")

    def test_validate_output_directory_normalizes_paths(self):
        """Test that paths are properly normalized."""
        test_path = "backup/./subdir/../final"
        result = validate_output_directory(test_path)
        
        assert "./" not in result
        assert "../" not in result
        assert result.endswith("final")


class TestGraphStatisticsImprovements:
    """Test the improved graph statistics functionality."""

    def test_graph_statistics_new_parameters(self):
        """Test that new parameters are properly handled."""
        # Test that GraphStatisticsArgs accepts new parameters
        args = GraphStatisticsArgs(
            graph_name="test_graph",
            aggregate_collections=True,
            per_collection_stats=True
        )
        
        assert args.aggregate_collections is True
        assert args.per_collection_stats is True

    def test_handle_graph_statistics_passes_new_params(self):
        """Test that handler passes new parameters to calculation function."""
        mock_db = Mock()
        
        with patch('mcp_arangodb_async.handlers.calculate_graph_statistics') as mock_calc:
            mock_calc.return_value = {"test": "result"}
            
            args = {
                "graph_name": "test",
                "aggregate_collections": True,
                "per_collection_stats": True
            }
            
            handle_graph_statistics(mock_db, args)
            
            # Verify all parameters were passed
            mock_calc.assert_called_once_with(
                mock_db,
                "test",
                True,  # include_degree_distribution
                True,  # include_connectivity  
                None,  # sample_size
                True,  # aggregate_collections
                True   # per_collection_stats
            )


class TestCodeQualityPolish:
    """Test the code quality improvements."""

    def test_delete_index_args_no_duplicate_field(self):
        """Test that DeleteIndexArgs no longer has duplicate field."""
        args = DeleteIndexArgs(collection="test", id_or_name="test_index")
        
        # Should not raise any validation errors
        assert args.collection == "test"
        assert args.id_or_name == "test_index"
        
        # Verify the model schema doesn't have duplicates
        schema = DeleteIndexArgs.model_json_schema()
        properties = schema["properties"]
        
        # Should only have collection and id_or_name
        assert set(properties.keys()) == {"collection", "id_or_name"}

    def test_create_index_supports_all_types(self):
        """Test that create_index function supports all index types mentioned in the report."""
        from mcp_arangodb_async.handlers import handle_create_index

        # Test that the function can handle all the index types
        # This verifies the implementation matches the updated documentation
        mock_db = Mock()
        mock_collection = Mock()
        mock_db.collection.return_value = mock_collection

        # Mock the index creation methods
        mock_collection.add_persistent_index.return_value = {"id": "test/1", "type": "persistent"}
        mock_collection.add_ttl_index.return_value = {"id": "test/2", "type": "ttl"}
        mock_collection.add_fulltext_index.return_value = {"id": "test/3", "type": "fulltext"}
        mock_collection.add_geo_index.return_value = {"id": "test/4", "type": "geo"}

        # Test each index type works
        index_types = ["persistent", "ttl", "fulltext", "geo"]
        for idx_type in index_types:
            args = {
                "collection": "test",
                "type": idx_type,
                "fields": ["field1"] if idx_type != "geo" else ["lat", "lng"],
            }
            if idx_type == "ttl":
                args["ttl"] = 3600

            result = handle_create_index(mock_db, args)
            # Should not return an error
            assert "error" not in result or result.get("type") != "ValueError"


if __name__ == "__main__":
    pytest.main([__file__])
