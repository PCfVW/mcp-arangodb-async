"""Integration tests for graph management tools through MCP protocol."""

import json
import pytest
from unittest.mock import Mock, patch
from mcp_arangodb_async import entry
from mcp_arangodb_async.entry import server


class TestGraphManagementIntegration:
    """Integration tests for new graph management tools through MCP interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_client = Mock()

    @pytest.mark.asyncio
    async def test_list_tools_includes_graph_management(self):
        """Test that new graph management tools appear in tool listings."""
        # Set environment to get full tool set
        with patch.dict('os.environ', {'MCP_COMPAT_TOOLSET': 'full'}):
            tools = await server._handlers["list_tools"]()
            
            tool_names = [tool.name for tool in tools]
            
            # Verify all new graph management tools are present
            expected_new_tools = [
                "arango_backup_graph",
                "arango_restore_graph", 
                "arango_backup_named_graphs",
                "arango_validate_graph_integrity",
                "arango_graph_statistics"
            ]
            
            for expected_tool in expected_new_tools:
                assert expected_tool in tool_names, f"Tool {expected_tool} not found in tool list"
            
            # Verify tool count increased appropriately
            assert len(tools) >= 24  # Original tools + 5 new graph tools

    @pytest.mark.asyncio
    async def test_graph_tool_schemas_generation(self):
        """Test that JSON schemas are properly generated for new graph tools."""
        with patch.dict('os.environ', {'MCP_COMPAT_TOOLSET': 'full'}):
            tools = await server._handlers["list_tools"]()
            
            graph_tools = {tool.name: tool for tool in tools if tool.name.startswith("arango_") and "graph" in tool.name}
            
            # Test backup graph tool schema
            backup_graph_tool = graph_tools.get("arango_backup_graph")
            assert backup_graph_tool is not None
            assert backup_graph_tool.inputSchema is not None
            
            schema = backup_graph_tool.inputSchema
            assert "properties" in schema
            assert "graph_name" in schema["properties"]
            assert schema["properties"]["graph_name"]["type"] == "string"
            assert "required" in schema
            assert "graph_name" in schema["required"]
            
            # Test restore graph tool schema
            restore_graph_tool = graph_tools.get("arango_restore_graph")
            assert restore_graph_tool is not None
            schema = restore_graph_tool.inputSchema
            assert "input_dir" in schema["properties"]
            assert "input_dir" in schema["required"]

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.handlers.handle_backup_graph')
    async def test_backup_graph_tool_success(self, mock_handler):
        """Test successful backup graph tool call through MCP."""
        mock_handler.return_value = {
            "graph_name": "test_graph",
            "output_dir": "/tmp/backup",
            "total_documents": 100,
            "metadata_included": True
        }
        
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}
            
            result = await server._handlers["call_tool"](
                "arango_backup_graph",
                {"graph_name": "test_graph", "output_dir": "/tmp/backup"}
            )
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data["graph_name"] == "test_graph"
            assert response_data["total_documents"] == 100
            
            mock_handler.assert_called_once()
            call_args = mock_handler.call_args[1]  # Get the args dict
            assert call_args["graph_name"] == "test_graph"
            assert call_args["output_dir"] == "/tmp/backup"

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.handlers.handle_restore_graph')
    async def test_restore_graph_tool_success(self, mock_handler):
        """Test successful restore graph tool call through MCP."""
        mock_handler.return_value = {
            "graph_name": "restored_graph",
            "graph_created": True,
            "total_documents_restored": 150,
            "errors": []
        }
        
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}
            
            result = await server._handlers["call_tool"](
                "arango_restore_graph",
                {
                    "input_dir": "/tmp/backup",
                    "conflict_resolution": "overwrite",
                    "validate_integrity": True
                }
            )
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data["graph_created"] is True
            assert response_data["total_documents_restored"] == 150
            
            mock_handler.assert_called_once()

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.handlers.handle_backup_named_graphs')
    async def test_backup_named_graphs_tool_success(self, mock_handler):
        """Test successful backup named graphs tool call through MCP."""
        mock_handler.return_value = {
            "output_file": "/tmp/graphs.json",
            "graphs_backed_up": 3,
            "missing_graphs": []
        }
        
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}
            
            result = await server._handlers["call_tool"](
                "arango_backup_named_graphs",
                {"graph_names": ["graph1", "graph2", "graph3"]}
            )
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data["graphs_backed_up"] == 3
            assert response_data["missing_graphs"] == []

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.handlers.handle_validate_graph_integrity')
    async def test_validate_graph_integrity_tool_success(self, mock_handler):
        """Test successful graph integrity validation tool call through MCP."""
        mock_handler.return_value = {
            "valid": True,
            "graphs_checked": 1,
            "total_orphaned_edges": 0,
            "total_constraint_violations": 0,
            "summary": "Checked 1 graphs: 0 orphaned edges, 0 violations"
        }
        
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}
            
            result = await server._handlers["call_tool"](
                "arango_validate_graph_integrity",
                {"graph_name": "test_graph", "return_details": True}
            )
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data["valid"] is True
            assert response_data["graphs_checked"] == 1

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.handlers.handle_graph_statistics')
    async def test_graph_statistics_tool_success(self, mock_handler):
        """Test successful graph statistics tool call through MCP."""
        mock_handler.return_value = {
            "graphs_analyzed": 1,
            "statistics": [{
                "graph_name": "test_graph",
                "total_vertices": 1000,
                "total_edges": 2500,
                "density": 0.005,
                "avg_out_degree": 2.5
            }],
            "analysis_timestamp": "2024-01-01T12:00:00"
        }
        
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}
            
            result = await server._handlers["call_tool"](
                "arango_graph_statistics",
                {
                    "graph_name": "test_graph",
                    "include_degree_distribution": True,
                    "sample_size": 100
                }
            )
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data["graphs_analyzed"] == 1
            assert len(response_data["statistics"]) == 1
            assert response_data["statistics"][0]["total_vertices"] == 1000

    @pytest.mark.asyncio
    async def test_graph_tool_validation_errors(self):
        """Test validation errors for graph management tools."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}
            
            # Test missing required field
            result = await server._handlers["call_tool"](
                "arango_backup_graph",
                {}  # Missing required graph_name
            )
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert "error" in response_data
            assert response_data["error"] == "ValidationError"
            assert "details" in response_data
            
            # Test invalid field value
            result = await server._handlers["call_tool"](
                "arango_backup_graph",
                {"graph_name": "test", "doc_limit": 0}  # doc_limit must be >= 1
            )
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert "error" in response_data
            assert response_data["error"] == "ValidationError"

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.handlers.handle_backup_graph')
    async def test_graph_tool_handler_errors(self, mock_handler):
        """Test error handling in graph management tools."""
        mock_handler.return_value = {
            "error": "Graph 'nonexistent' does not exist",
            "type": "GraphNotFound"
        }
        
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}
            
            result = await server._handlers["call_tool"](
                "arango_backup_graph",
                {"graph_name": "nonexistent"}
            )
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert "error" in response_data
            assert response_data["type"] == "GraphNotFound"

    @pytest.mark.asyncio
    async def test_graph_tools_with_aliases(self):
        """Test graph management tools work with field aliases."""
        with patch('mcp_arangodb_async.handlers.handle_backup_graph') as mock_handler:
            mock_handler.return_value = {"graph_name": "test", "total_documents": 50}
            
            with patch.object(server, 'request_context') as mock_ctx:
                mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}
                
                # Test using aliases (camelCase)
                result = await server._handlers["call_tool"](
                    "arango_backup_graph",
                    {
                        "graph_name": "test_graph",
                        "outputDir": "/tmp/backup",  # alias for output_dir
                        "includeMetadata": False,    # alias for include_metadata
                        "docLimit": 100             # alias for doc_limit
                    }
                )
                
                assert len(result) == 1
                response_data = json.loads(result[0].text)
                assert response_data["graph_name"] == "test"
                
                # Verify handler was called with correct arguments
                mock_handler.assert_called_once()
                call_args = mock_handler.call_args[1]
                assert call_args["output_dir"] == "/tmp/backup"
                assert call_args["include_metadata"] is False
                assert call_args["doc_limit"] == 100
