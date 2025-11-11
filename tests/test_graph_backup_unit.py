"""Unit tests for graph backup utilities."""

import json
import os
import pytest
from tempfile import TemporaryDirectory
from unittest.mock import Mock, MagicMock, patch, mock_open, ANY

from mcp_arangodb_async.graph_backup import (
    backup_graph_to_dir,
    restore_graph_from_dir,
    backup_named_graphs,
    validate_graph_integrity,
    calculate_graph_statistics,
    _backup_collection_to_file,
    _restore_collection_from_file,
)


class TestBackupGraphToDir:
    """Test cases for backup_graph_to_dir function."""

    def test_backup_graph_success(self):
        """Test successful graph backup."""
        # Mock database and graph
        mock_db = Mock()
        mock_graph = Mock()
        mock_db.has_graph.return_value = True
        mock_db.graph.return_value = mock_graph
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "name": "test_graph",
            "edge_definitions": [
                {
                    "edge_collection": "follows",
                    "from_vertex_collections": ["users"],
                    "to_vertex_collections": ["users"]
                }
            ],
            "orphan_collections": ["posts"]
        }
        
        # Mock collections
        mock_db.has_collection.return_value = True
        
        with TemporaryDirectory() as tmp_dir:
            with patch('mcp_arangodb_async.graph_backup._backup_collection_to_file') as mock_backup_col:
                mock_backup_col.return_value = 10  # 10 documents backed up
                
                result = backup_graph_to_dir(mock_db, "test_graph", tmp_dir)
                
                assert result["graph_name"] == "test_graph"
                assert result["output_dir"] == tmp_dir
                assert result["total_vertex_collections"] == 2  # users, posts
                assert result["total_edge_collections"] == 1   # follows
                assert result["total_documents"] == 30  # 3 collections * 10 docs
                assert result["metadata_included"] is True
                
                # Verify directories were created
                assert os.path.exists(os.path.join(tmp_dir, "vertices"))
                assert os.path.exists(os.path.join(tmp_dir, "edges"))
                assert os.path.exists(os.path.join(tmp_dir, "graph_metadata.json"))
                assert os.path.exists(os.path.join(tmp_dir, "backup_report.json"))

    def test_backup_graph_nonexistent_graph(self):
        """Test backup of non-existent graph raises error."""
        mock_db = Mock()
        mock_db.has_graph.return_value = False
        
        with pytest.raises(ValueError, match="Graph 'nonexistent' does not exist"):
            backup_graph_to_dir(mock_db, "nonexistent")

    def test_backup_graph_with_doc_limit(self):
        """Test graph backup with document limit."""
        mock_db = Mock()
        mock_graph = Mock()
        mock_db.has_graph.return_value = True
        mock_db.graph.return_value = mock_graph
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "edge_definitions": [{"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}],
            "orphan_collections": []
        }
        mock_db.has_collection.return_value = True
        
        with TemporaryDirectory() as tmp_dir:
            with patch('mcp_arangodb_async.graph_backup._backup_collection_to_file') as mock_backup_col:
                mock_backup_col.return_value = 5  # Limited to 5 documents
                
                result = backup_graph_to_dir(mock_db, "test_graph", tmp_dir, doc_limit=5)
                
                # Verify doc_limit was passed to backup function for both collections
                assert mock_backup_col.call_count == 2
                calls = mock_backup_col.call_args_list
                # Check that both vertices and edges were backed up with doc_limit=5
                call_collections = [call[0][1] for call in calls]  # Extract collection names
                assert "vertices" in call_collections
                assert "edges" in call_collections
                # Verify doc_limit parameter for all calls
                for call in calls:
                    assert call[0][3] == 5  # doc_limit parameter

    def test_backup_graph_without_metadata(self):
        """Test graph backup without metadata."""
        mock_db = Mock()
        mock_graph = Mock()
        mock_db.has_graph.return_value = True
        mock_db.graph.return_value = mock_graph
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "edge_definitions": [],
            "orphan_collections": ["test_col"]
        }
        mock_db.has_collection.return_value = True
        
        with TemporaryDirectory() as tmp_dir:
            with patch('mcp_arangodb_async.graph_backup._backup_collection_to_file') as mock_backup_col:
                mock_backup_col.return_value = 0
                
                result = backup_graph_to_dir(mock_db, "test_graph", tmp_dir, include_metadata=False)
                
                assert result["metadata_included"] is False
                assert not os.path.exists(os.path.join(tmp_dir, "graph_metadata.json"))


class TestRestoreGraphFromDir:
    """Test cases for restore_graph_from_dir function."""

    def test_restore_graph_success(self):
        """Test successful graph restore."""
        mock_db = Mock()
        mock_db.has_graph.return_value = False  # Graph doesn't exist yet
        mock_db.create_graph.return_value = Mock()
        
        # Mock metadata file
        # Note: python-arango returns snake_case keys, not camelCase
        metadata = {
            "graph_name": "test_graph",
            "graph_properties": {
                "edge_definitions": [{"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}],
                "orphan_collections": []
            }
        }
        
        with TemporaryDirectory() as tmp_dir:
            # Create mock backup structure
            os.makedirs(os.path.join(tmp_dir, "vertices"))
            os.makedirs(os.path.join(tmp_dir, "edges"))
            
            with open(os.path.join(tmp_dir, "graph_metadata.json"), "w") as f:
                json.dump(metadata, f)
            
            with open(os.path.join(tmp_dir, "vertices", "vertices.json"), "w") as f:
                json.dump([{"_key": "1", "name": "test"}], f)
            
            with open(os.path.join(tmp_dir, "edges", "edges.json"), "w") as f:
                json.dump([{"_key": "1", "_from": "vertices/1", "_to": "vertices/1"}], f)
            
            with patch('mcp_arangodb_async.graph_backup._restore_collection_from_file') as mock_restore_col:
                mock_restore_col.return_value = {"collection": "test", "inserted": 1, "updated": 0, "skipped": 0, "errors": 0, "total_processed": 1}

                with patch('mcp_arangodb_async.graph_backup.validate_graph_integrity') as mock_validate:
                    mock_validate.return_value = {"valid": True}
                    
                    result = restore_graph_from_dir(mock_db, tmp_dir)
                    
                    assert result["graph_name"] == "test_graph"
                    assert result["original_graph_name"] == "test_graph"
                    assert result["graph_created"] is True
                    assert len(result["restored_vertices"]) == 1
                    assert len(result["restored_edges"]) == 1
                    assert result["total_documents_restored"] == 2

    def test_restore_graph_missing_metadata(self):
        """Test restore with missing metadata file."""
        with TemporaryDirectory() as tmp_dir:
            with pytest.raises(ValueError, match="Invalid backup: graph_metadata.json not found"):
                restore_graph_from_dir(Mock(), tmp_dir)

    def test_restore_graph_conflict_error(self):
        """Test restore with existing graph and error conflict resolution."""
        mock_db = Mock()
        mock_db.has_graph.return_value = True  # Graph already exists

        # Note: python-arango returns snake_case keys, not camelCase
        metadata = {
            "graph_name": "existing_graph",
            "graph_properties": {"edge_definitions": [], "orphan_collections": []}
        }
        
        with TemporaryDirectory() as tmp_dir:
            with open(os.path.join(tmp_dir, "graph_metadata.json"), "w") as f:
                json.dump(metadata, f)
            
            result = restore_graph_from_dir(mock_db, tmp_dir, conflict_resolution="error")
            
            assert result["graph_created"] is False
            assert len(result["errors"]) > 0
            assert "already exists" in result["errors"][0]["error"]


class TestBackupNamedGraphs:
    """Test cases for backup_named_graphs function."""

    def test_backup_named_graphs_all(self):
        """Test backing up all named graphs."""
        mock_db = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_db.graphs.return_value = [
            {"name": "graph1", "edge_definitions": []},
            {"name": "graph2", "edge_definitions": []}
        ]
        
        with TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, "graphs.json")
            
            result = backup_named_graphs(mock_db, output_file)
            
            assert result["output_file"] == output_file
            assert result["graphs_backed_up"] == 2
            assert result["missing_graphs"] == []
            assert os.path.exists(output_file)
            
            # Verify file contents
            with open(output_file, "r") as f:
                data = json.load(f)
            assert data["total_graphs"] == 2
            assert len(data["graphs"]) == 2

    def test_backup_named_graphs_specific(self):
        """Test backing up specific named graphs."""
        mock_db = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_db.graphs.return_value = [
            {"name": "graph1", "edge_definitions": []},
            {"name": "graph2", "edge_definitions": []}
        ]
        
        with TemporaryDirectory() as tmp_dir:
            output_file = os.path.join(tmp_dir, "specific.json")
            
            result = backup_named_graphs(mock_db, output_file, ["graph1", "nonexistent"])
            
            assert result["graphs_backed_up"] == 1
            assert result["missing_graphs"] == ["nonexistent"]


class TestValidateGraphIntegrity:
    """Test cases for validate_graph_integrity function."""

    def test_validate_graph_integrity_success(self):
        """Test successful graph integrity validation."""
        mock_db = Mock()
        mock_db.graphs.return_value = [{"name": "test_graph"}]
        mock_db.has_graph.return_value = True
        
        mock_graph = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "edge_definitions": [{"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}]
        }
        mock_db.graph.return_value = mock_graph
        mock_db.has_collection.return_value = True
        
        # Mock AQL query that returns no orphaned edges
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter([]))
        mock_db.aql.execute.return_value = mock_cursor
        
        result = validate_graph_integrity(mock_db, "test_graph")
        
        assert result["valid"] is True
        assert result["graphs_checked"] == 1
        assert result["total_orphaned_edges"] == 0
        assert len(result["results"]) == 1
        assert result["results"][0]["valid"] is True

    def test_validate_graph_integrity_with_orphans(self):
        """Test graph integrity validation with orphaned edges."""
        mock_db = Mock()
        mock_db.graphs.return_value = [{"name": "test_graph"}]
        mock_db.has_graph.return_value = True

        mock_graph = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "edge_definitions": [{"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}]
        }
        mock_db.graph.return_value = mock_graph
        mock_db.has_collection.return_value = True

        # Mock AQL query that returns orphaned edges
        orphaned_edge = {
            "_id": "edges/1",
            "_from": "vertices/missing",
            "_to": "vertices/1",
            "from_exists": False,
            "to_exists": True
        }
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter([orphaned_edge]))
        mock_db.aql.execute.return_value = mock_cursor

        result = validate_graph_integrity(mock_db, "test_graph", return_details=True)

        assert result["valid"] is False
        assert result["total_orphaned_edges"] == 1
        assert len(result["results"][0]["orphaned_edges"]) == 1

    def test_validate_graph_integrity_with_constraint_violations(self):
        """Test that constraint violations are properly counted in totals."""
        mock_db = Mock()
        mock_db.graphs.return_value = [{"name": "test_graph"}]
        mock_db.has_graph.return_value = True

        mock_graph = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "edge_definitions": [{"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}]
        }
        mock_db.graph.return_value = mock_graph
        mock_db.has_collection.return_value = True

        # Mock AQL query that raises an exception (constraint violation)
        mock_db.aql.execute.side_effect = Exception("Query failed")

        result = validate_graph_integrity(mock_db, "test_graph", return_details=True)

        assert result["valid"] is False
        assert result["total_constraint_violations"] == 1
        assert result["total_orphaned_edges"] == 0
        assert len(result["results"][0]["constraint_violations"]) == 1
        assert result["results"][0]["constraint_violations"][0]["type"] == "query_error"

    def test_validate_graph_integrity_multiple_graphs_accumulates_totals(self):
        """Test that totals are properly accumulated across multiple graphs."""
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

        assert result["valid"] is False
        assert result["total_orphaned_edges"] == 1
        assert result["total_constraint_violations"] == 1
        assert result["graphs_checked"] == 2
        assert "1 orphaned edges, 1 violations" in result["summary"]


class TestCalculateGraphStatistics:
    """Test cases for calculate_graph_statistics function."""

    def test_calculate_graph_statistics_success(self):
        """Test successful graph statistics calculation."""
        mock_db = Mock()
        mock_db.graphs.return_value = [{"name": "test_graph"}]
        mock_db.has_graph.return_value = True
        
        mock_graph = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "edge_definitions": [{"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}],
            "orphan_collections": []
        }
        mock_db.graph.return_value = mock_graph
        mock_db.has_collection.return_value = True
        
        # Mock collection counts
        mock_collection = Mock()
        mock_collection.count.return_value = 100
        mock_db.collection.return_value = mock_collection
        
        # Mock degree distribution query
        degree_data = [{"degree": 1, "frequency": 50}, {"degree": 2, "frequency": 30}]
        mock_cursor = Mock()
        mock_cursor.__iter__ = Mock(return_value=iter(degree_data))
        mock_db.aql.execute.return_value = mock_cursor
        
        result = calculate_graph_statistics(mock_db, "test_graph")
        
        assert result["graphs_analyzed"] == 1
        assert len(result["statistics"]) == 1
        
        stats = result["statistics"][0]
        assert stats["graph_name"] == "test_graph"
        assert stats["total_vertices"] == 100
        assert stats["total_edges"] == 100
        assert "density" in stats
        assert "out_degree_distribution" in stats

    def test_calculate_graph_statistics_no_graphs(self):
        """Test graph statistics with no graphs found."""
        mock_db = Mock()
        mock_db.graphs.return_value = []
        
        result = calculate_graph_statistics(mock_db)
        
        assert "error" in result
        assert result["type"] == "NoGraphsFound"
