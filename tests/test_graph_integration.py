"""Integration tests for graph management tools through MCP protocol."""

import json
import pytest
from unittest.mock import Mock, patch, mock_open
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
            assert "inputDir" in schema["properties"]
            assert "inputDir" in schema["required"]

    @pytest.mark.asyncio
    async def test_backup_graph_tool_success(self):
        """Test successful backup graph tool call through MCP."""
        # Set up mock database for graph operations
        mock_graph = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "name": "test_graph",
            "edge_definitions": [
                {
                    "edge_collection": "edges",
                    "from_vertex_collections": ["vertices"],
                    "to_vertex_collections": ["vertices"]
                }
            ],
            "orphan_collections": []
        }

        self.mock_db.has_graph.return_value = True
        self.mock_db.graph.return_value = mock_graph
        self.mock_db.has_collection.return_value = True

        # Mock collection for backup
        mock_collection = Mock()
        mock_collection.count.return_value = 50
        self.mock_db.collection.return_value = mock_collection

        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            # Mock the file operations
            with patch('mcp_arangodb_async.graph_backup._backup_collection_to_file') as mock_backup_file:
                mock_backup_file.return_value = 50

                result = await server._handlers["call_tool"](
                    "arango_backup_graph",
                    {"graph_name": "test_graph", "output_dir": "/tmp/backup"}
                )

                assert len(result) == 1
                response_data = json.loads(result[0].text)
                assert response_data["graph_name"] == "test_graph"
                assert response_data["total_documents"] == 100  # 50 vertices + 50 edges

    @pytest.mark.asyncio
    async def test_restore_graph_tool_success(self):
        """Test successful restore graph tool call through MCP."""
        # Set up mock database for restore operations
        self.mock_db.has_graph.return_value = False  # Graph doesn't exist yet
        self.mock_db.create_graph.return_value = Mock()
        self.mock_db.has_collection.return_value = False  # Collections don't exist yet
        self.mock_db.create_collection.return_value = Mock()

        # Mock collection for restore
        mock_collection = Mock()
        mock_collection.insert_many.return_value = {"new": 75}  # 75 documents inserted
        self.mock_db.collection.return_value = mock_collection

        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            # Mock the file operations and directory existence
            with patch('os.path.exists') as mock_exists, \
                 patch('os.listdir') as mock_listdir, \
                 patch('mcp_arangodb_async.graph_backup._restore_collection_from_file') as mock_restore_file:

                mock_exists.return_value = True  # Directory exists
                mock_listdir.return_value = ['metadata.json', 'vertices', 'edges']
                mock_restore_file.return_value = {"inserted": 75, "updated": 0}  # 75 documents restored per collection

                # Mock metadata file reading
                # Note: python-arango returns snake_case keys, not camelCase
                metadata = {
                    "graph_name": "test_graph",
                    "graph_properties": {
                        "name": "test_graph",
                        "edge_definitions": [{"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}],
                        "orphan_collections": []
                    }
                }
                with patch('builtins.open', mock_open(read_data=json.dumps(metadata))):
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
                    assert response_data["total_documents_restored"] == 150  # 75 vertices + 75 edges

    @pytest.mark.asyncio
    async def test_backup_named_graphs_tool_success(self):
        """Test successful backup named graphs tool call through MCP."""
        # Set up mock database with iterable graphs as dictionaries
        # Note: python-arango returns snake_case keys, not camelCase
        graph_data = [
            {"name": "graph1", "edge_definitions": [], "orphan_collections": []},
            {"name": "graph2", "edge_definitions": [], "orphan_collections": []},
            {"name": "graph3", "edge_definitions": [], "orphan_collections": []}
        ]

        # Make graphs() return an iterable list of dictionaries
        self.mock_db.graphs.return_value = graph_data

        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            # Mock file operations
            with patch('builtins.open', mock_open()) as mock_file, \
                 patch('os.path.getsize', return_value=1024):  # Mock file size
                result = await server._handlers["call_tool"](
                    "arango_backup_named_graphs",
                    {"graph_names": ["graph1", "graph2", "graph3"]}
                )

                assert len(result) == 1
                response_data = json.loads(result[0].text)
                assert response_data["graphs_backed_up"] == 3
                assert response_data["missing_graphs"] == []

    @pytest.mark.asyncio
    async def test_validate_graph_integrity_tool_success(self):
        """Test successful graph integrity validation tool call through MCP."""
        # Set up mock database with proper graph structure
        mock_graph = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "name": "test_graph",
            "edge_definitions": [
                {"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}
            ],
            "orphan_collections": []
        }
        self.mock_db.has_graph.return_value = True
        self.mock_db.graph.return_value = mock_graph

        # Mock collections for integrity checking
        mock_edge_collection = Mock()
        mock_edge_collection.all.return_value = []  # No edges to check
        mock_vertex_collection = Mock()
        mock_vertex_collection.all.return_value = []  # No vertices to check

        self.mock_db.has_collection.return_value = True
        self.mock_db.collection.side_effect = lambda name: mock_edge_collection if name == "edges" else mock_vertex_collection

        # Mock AQL query execution to return empty results (no violations)
        self.mock_db.aql.execute.return_value = []  # No orphaned edges or constraint violations

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
    async def test_graph_statistics_tool_success(self):
        """Test successful graph statistics tool call through MCP."""
        # Set up mock database with proper graph structure
        mock_graph = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "name": "test_graph",
            "edge_definitions": [
                {"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}
            ],
            "orphan_collections": []
        }
        self.mock_db.has_graph.return_value = True
        self.mock_db.graph.return_value = mock_graph

        # Mock collections for statistics
        mock_edge_collection = Mock()
        mock_edge_collection.count.return_value = 2500  # Total edges
        mock_vertex_collection = Mock()
        mock_vertex_collection.count.return_value = 1000  # Total vertices

        self.mock_db.has_collection.return_value = True
        self.mock_db.collection.side_effect = lambda name: mock_edge_collection if name == "edges" else mock_vertex_collection

        # Mock AQL query execution for degree distribution
        self.mock_db.aql.execute.return_value = [
            {"degree": 1, "count": 400},
            {"degree": 2, "count": 300},
            {"degree": 3, "count": 200},
            {"degree": 4, "count": 100}
        ]

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
    async def test_graph_tool_handler_errors(self):
        """Test error handling in graph management tools."""
        # Set up mock database to simulate nonexistent graph
        self.mock_db.has_graph.return_value = False  # Graph doesn't exist

        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                "arango_backup_graph",
                {"graph_name": "nonexistent"}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert "error" in response_data
            # The actual error message will be about the graph not existing
            assert "nonexistent" in response_data["error"] or "not exist" in response_data["error"]

    @pytest.mark.asyncio
    async def test_graph_tools_with_aliases(self):
        """Test graph management tools work with field aliases."""
        # Set up mock database with proper graph structure
        mock_graph = Mock()
        # Note: python-arango returns snake_case keys, not camelCase
        mock_graph.properties.return_value = {
            "name": "test_graph",
            "edge_definitions": [
                {"edge_collection": "edges", "from_vertex_collections": ["vertices"], "to_vertex_collections": ["vertices"]}
            ],
            "orphan_collections": []
        }
        self.mock_db.has_graph.return_value = True
        self.mock_db.graph.return_value = mock_graph

        # Mock collections for backup
        mock_edge_collection = Mock()
        mock_edge_collection.all.return_value = [{"_id": "edges/1", "_from": "vertices/1", "_to": "vertices/2"}]
        mock_vertex_collection = Mock()
        mock_vertex_collection.all.return_value = [{"_id": "vertices/1", "name": "vertex1"}]

        self.mock_db.has_collection.return_value = True
        self.mock_db.collection.side_effect = lambda name: mock_edge_collection if name == "edges" else mock_vertex_collection

        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            # Mock file operations
            with patch('builtins.open', mock_open()) as mock_file:
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
                assert response_data["graph_name"] == "test_graph"
                assert response_data["total_documents"] > 0  # Should have backed up some documents
