"""Integration tests for MCP server functionality."""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock, mock_open
from mcp_arangodb_async.entry import server, _json_content
from mcp_arangodb_async.models import QueryArgs, InsertArgs, BackupArgs
from mcp_arangodb_async.tools import (
    ARANGO_SEARCH_TOOLS,
    ARANGO_LIST_TOOLS_BY_CATEGORY,
    ARANGO_SWITCH_CONTEXT,
    ARANGO_GET_ACTIVE_CONTEXT,
    ARANGO_LIST_CONTEXTS,
    ARANGO_ADVANCE_WORKFLOW_STAGE,
    ARANGO_GET_TOOL_USAGE_STATS,
    ARANGO_UNLOAD_TOOLS,
)
import mcp.types as types


class TestMCPIntegration:
    """Test MCP server integration and tool execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_client = Mock()

    def test_json_content_helper(self):
        """Test JSON content conversion helper."""
        data = {"test": "value", "number": 42}
        result = _json_content(data)
        
        assert len(result) == 1
        assert isinstance(result[0], types.TextContent)
        assert result[0].type == "text"
        
        parsed_data = json.loads(result[0].text)
        assert parsed_data == {"test": "value", "number": 42}

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test MCP tool listing."""
        tools = await server._handlers["list_tools"]()

        assert len(tools) == 7
        tool_names = [tool.name for tool in tools]

        expected_tools = [
            "arango_query",
            "arango_list_collections",
            "arango_insert",
            "arango_update",
            "arango_remove",
            "arango_create_collection",
            "arango_backup"
        ]

        for expected in expected_tools:
            assert expected in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_full_set(self):
        """Test MCP tool listing with full tool set including new graph management tools."""
        with patch.dict('os.environ', {'MCP_COMPAT_TOOLSET': 'full'}):
            tools = await server._handlers["list_tools"]()

            tool_names = [tool.name for tool in tools]

            # Test that new graph management tools are included
            new_graph_tools = [
                "arango_backup_graph",
                "arango_restore_graph",
                "arango_backup_named_graphs",
                "arango_validate_graph_integrity",
                "arango_graph_statistics"
            ]

            for tool in new_graph_tools:
                assert tool in tool_names, f"New graph tool {tool} not found in tool list"

            # Verify we have significantly more tools now
            assert len(tools) >= 24  # Original + new graph tools

    @pytest.mark.asyncio
    async def test_call_tool_validation_error(self):
        """Test tool call with validation error."""
        # Mock server context
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}
            
            # Call with invalid arguments (missing required query)
            result = await server._handlers["call_tool"]("arango_query", {})
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert "error" in response_data
            assert response_data["error"] == "ValidationError"

    @pytest.mark.asyncio
    async def test_call_tool_database_unavailable(self):
        """Test tool call when database is unavailable."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": None, "client": None}

            # Mock get_client_and_db to raise an exception so lazy connection fails
            with patch('mcp_arangodb_async.entry.get_client_and_db') as mock_get_db:
                mock_get_db.side_effect = Exception("Connection failed")

                result = await server._handlers["call_tool"]("arango_query", {"query": "RETURN 1"})

                assert len(result) == 1
                response_data = json.loads(result[0].text)
                assert response_data["error"] == "Database unavailable"

    @pytest.mark.asyncio
    async def test_call_tool_query_success(self):
        """Test successful query tool call."""
        # Setup mock database to return iterable cursor
        mock_cursor = [{"result": "success"}]
        self.mock_db.aql.execute.return_value = mock_cursor

        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"]("arango_query", {
                "query": "RETURN 1",
                "bind_vars": {"test": "value"}
            })

            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data == [{"result": "success"}]

            # Verify database was called with correct query
            self.mock_db.aql.execute.assert_called_once_with(
                "RETURN 1",
                bind_vars={"test": "value"}
            )

    @pytest.mark.asyncio
    async def test_call_tool_list_collections_success(self):
        """Test successful list collections tool call."""
        # Setup mock database to return iterable collections
        mock_collections = [
            {"name": "users", "isSystem": False},
            {"name": "products", "isSystem": False},
            {"name": "_system", "isSystem": True}  # Should be filtered out
        ]
        self.mock_db.collections.return_value = mock_collections

        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"]("arango_list_collections", {})

            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data == ["users", "products"]

    @pytest.mark.asyncio
    async def test_call_tool_insert_success(self):
        """Test successful insert tool call."""
        # Setup mock collection to return insert result
        mock_collection = Mock()
        mock_collection.insert.return_value = {"_id": "users/123", "_key": "123", "_rev": "_abc"}
        self.mock_db.collection.return_value = mock_collection

        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"]("arango_insert", {
                "collection": "users",
                "document": {"name": "John", "age": 30}
            })

            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data["_id"] == "users/123"

    @pytest.mark.asyncio
    async def test_call_tool_unknown_tool(self):
        """Test call to unknown tool."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}
            
            result = await server._handlers["call_tool"]("unknown_tool", {})
            
            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert "Unknown tool" in response_data["error"]

    @pytest.mark.asyncio
    async def test_call_tool_handler_exception(self):
        """Test tool call when handler raises exception."""
        # Setup mock database to raise exception when executing query
        self.mock_db.aql.execute.side_effect = Exception("Handler error")

        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"]("arango_query", {"query": "RETURN 1"})

            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data["error"] == "Handler error"
            assert response_data["tool"] == "arango_query"

    @pytest.mark.asyncio
    async def test_call_tool_backup_graph_success(self):
        """Test successful backup graph tool call."""
        # Setup mock database with proper graph structure
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

            with patch('builtins.open', mock_open()) as mock_file:
                result = await server._handlers["call_tool"](
                    "arango_backup_graph",
                    {"graph_name": "test_graph", "output_dir": "/tmp/backup"}
                )

                assert len(result) == 1
                response_data = json.loads(result[0].text)
                assert response_data["graph_name"] == "test_graph"
                assert response_data["total_documents"] > 0

    @pytest.mark.asyncio
    async def test_call_tool_backup_graph_validation_error(self):
        """Test backup graph tool call with validation error."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            # Missing required graph_name field
            result = await server._handlers["call_tool"]("arango_backup_graph", {})

            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert "error" in response_data
            assert response_data["error"] == "ValidationError"
            assert "details" in response_data

    @pytest.mark.asyncio
    async def test_call_tool_graph_statistics_with_aliases(self):
        """Test graph statistics tool call with field aliases."""
        # Setup mock database with proper graph structure
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

        # Mock collections with proper count methods
        mock_vertex_collection = Mock()
        mock_vertex_collection.count.return_value = 10
        mock_edge_collection = Mock()
        mock_edge_collection.count.return_value = 5

        self.mock_db.has_collection.return_value = True
        self.mock_db.collection.side_effect = lambda name: mock_edge_collection if name == "edges" else mock_vertex_collection

        # Mock AQL query execution for statistics
        self.mock_db.aql.execute.return_value = []

        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            # Use aliases (camelCase)
            result = await server._handlers["call_tool"](
                "arango_graph_statistics",
                {
                    "graphName": "test_graph",  # alias for graph_name
                    "includeDegreeDistribution": False,  # alias for include_degree_distribution
                    "sampleSize": 200  # alias for sample_size
                }
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)
            assert response_data["graphs_analyzed"] == 1


class TestServerLifespan:
    """Test server lifespan management."""

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.entry.load_config')
    @patch('mcp_arangodb_async.entry.get_client_and_db')
    async def test_server_lifespan_success(self, mock_get_client, mock_load_config):
        """Test successful server lifespan initialization."""
        from mcp_arangodb_async.entry import server_lifespan
        
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_client = Mock()
        mock_db = Mock()
        mock_get_client.return_value = (mock_client, mock_db)
        
        # Test lifespan context manager
        async with server_lifespan(server) as context:
            assert context["db"] == mock_db
            assert context["client"] == mock_client
        
        # Verify cleanup
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.entry.load_config')
    @patch('mcp_arangodb_async.entry.get_client_and_db')
    async def test_server_lifespan_connection_failure(self, mock_get_client, mock_load_config):
        """Test server lifespan with connection failure."""
        from mcp_arangodb_async.entry import server_lifespan
        
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_get_client.side_effect = Exception("Connection failed")
        
        # Test lifespan context manager with connection failure
        async with server_lifespan(server) as context:
            assert context["db"] is None
            assert context["client"] is None

    @pytest.mark.asyncio
    @patch('mcp_arangodb_async.entry.load_config')
    @patch('mcp_arangodb_async.entry.get_client_and_db')
    async def test_server_lifespan_retry_logic(self, mock_get_client, mock_load_config):
        """Test server lifespan retry logic."""
        from mcp_arangodb_async.entry import server_lifespan
        
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_client = Mock()
        mock_db = Mock()
        
        # First call fails, second succeeds
        mock_get_client.side_effect = [
            Exception("First attempt failed"),
            (mock_client, mock_db)
        ]
        
        with patch.dict('os.environ', {'ARANGO_CONNECT_RETRIES': '2', 'ARANGO_CONNECT_DELAY_SEC': '0.01'}):
            async with server_lifespan(server) as context:
                assert context["db"] == mock_db
                assert context["client"] == mock_client

        # Verify retry happened
        assert mock_get_client.call_count == 2


class TestMCPDesignPatternToolsIntegration:
    """Integration tests for MCP Design Pattern tools through the MCP server."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_client = Mock()

    # ========================================================================
    # Pattern 1: Progressive Tool Discovery
    # ========================================================================

    @pytest.mark.asyncio
    async def test_search_tools_by_keywords(self):
        """Test arango_search_tools through MCP server."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_SEARCH_TOOLS,
                {
                    "keywords": ["query", "graph"],
                    "categories": None,
                    "detail_level": "summary"
                }
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert "matches" in response_data
            assert "total_matches" in response_data
            assert "keywords" in response_data
            assert response_data["keywords"] == ["query", "graph"]
            assert response_data["detail_level"] == "summary"
            assert response_data["total_matches"] > 0

    @pytest.mark.asyncio
    async def test_search_tools_with_category_filter(self):
        """Test arango_search_tools with category filter."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_SEARCH_TOOLS,
                {
                    "keywords": ["insert"],
                    "categories": ["core_data"],
                    "detail_level": "name"
                }
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert response_data["categories_searched"] == ["core_data"]
            assert response_data["detail_level"] == "name"

    @pytest.mark.asyncio
    async def test_search_tools_full_detail(self):
        """Test arango_search_tools with full detail level."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_SEARCH_TOOLS,
                {
                    "keywords": ["query"],
                    "categories": None,
                    "detail_level": "full"
                }
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert response_data["detail_level"] == "full"
            # Verify at least one match has inputSchema
            if response_data["total_matches"] > 0:
                first_match = response_data["matches"][0]
                assert "name" in first_match
                assert "description" in first_match
                assert "inputSchema" in first_match

    @pytest.mark.asyncio
    async def test_list_tools_by_category_all(self):
        """Test arango_list_tools_by_category for all categories."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_LIST_TOOLS_BY_CATEGORY,
                {"category": None}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert "categories" in response_data
            assert "total_tools" in response_data
            assert len(response_data["categories"]) == 9  # 9 categories
            assert "core_data" in response_data["categories"]
            assert "graph_basic" in response_data["categories"]

    @pytest.mark.asyncio
    async def test_list_tools_by_category_single(self):
        """Test arango_list_tools_by_category for single category."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_LIST_TOOLS_BY_CATEGORY,
                {"category": "core_data"}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert response_data["category"] == "core_data"
            assert "tools" in response_data
            assert "tool_count" in response_data
            assert response_data["tool_count"] > 0

    @pytest.mark.asyncio
    async def test_list_tools_by_category_invalid(self):
        """Test arango_list_tools_by_category with invalid category."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_LIST_TOOLS_BY_CATEGORY,
                {"category": "invalid_category"}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert "error" in response_data
            assert "available_categories" in response_data

    # ========================================================================
    # Pattern 2: Context Switching
    # ========================================================================

    @pytest.mark.asyncio
    async def test_list_contexts(self):
        """Test arango_list_contexts through MCP server."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_LIST_CONTEXTS,
                {"include_tools": False}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert "contexts" in response_data
            assert "total_contexts" in response_data
            assert "active_context" in response_data
            assert len(response_data["contexts"]) == 6  # 6 workflow contexts

    @pytest.mark.asyncio
    async def test_list_contexts_with_tools(self):
        """Test arango_list_contexts with tool details."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_LIST_CONTEXTS,
                {"include_tools": True}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert len(response_data["contexts"]) == 6
            # Verify each context includes tools list
            for context_name, context_info in response_data["contexts"].items():
                assert "description" in context_info
                assert "tool_count" in context_info
                assert "tools" in context_info

    @pytest.mark.asyncio
    async def test_switch_context_valid(self):
        """Test arango_switch_context with valid context."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_SWITCH_CONTEXT,
                {"context": "graph_modeling"}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert "from_context" in response_data
            assert "to_context" in response_data
            assert response_data["to_context"] == "graph_modeling"
            assert "description" in response_data
            assert "tools_added" in response_data
            assert "tools_removed" in response_data
            assert "active_tools" in response_data

    @pytest.mark.asyncio
    async def test_switch_context_invalid(self):
        """Test arango_switch_context with invalid context."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_SWITCH_CONTEXT,
                {"context": "invalid_context"}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            # Pydantic validation error occurs before handler is called
            assert "error" in response_data
            assert response_data["error"] == "ValidationError"

    @pytest.mark.asyncio
    async def test_get_active_context(self):
        """Test arango_get_active_context through MCP server."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            # First switch to a known context
            await server._handlers["call_tool"](
                ARANGO_SWITCH_CONTEXT,
                {"context": "bulk_operations"}
            )

            # Now get active context
            result = await server._handlers["call_tool"](
                ARANGO_GET_ACTIVE_CONTEXT,
                {}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert "active_context" in response_data
            assert response_data["active_context"] == "bulk_operations"
            assert "description" in response_data
            assert "tools" in response_data
            assert "tool_count" in response_data

    @pytest.mark.asyncio
    async def test_context_switching_workflow(self):
        """Test complete context switching workflow."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            # Switch to data_analysis
            result1 = await server._handlers["call_tool"](
                ARANGO_SWITCH_CONTEXT,
                {"context": "data_analysis"}
            )
            data1 = json.loads(result1[0].text)
            assert data1["to_context"] == "data_analysis"

            # Switch to graph_modeling
            result2 = await server._handlers["call_tool"](
                ARANGO_SWITCH_CONTEXT,
                {"context": "graph_modeling"}
            )
            data2 = json.loads(result2[0].text)
            assert data2["from_context"] == "data_analysis"
            assert data2["to_context"] == "graph_modeling"

            # Verify active context
            result3 = await server._handlers["call_tool"](
                ARANGO_GET_ACTIVE_CONTEXT,
                {}
            )
            data3 = json.loads(result3[0].text)
            assert data3["active_context"] == "graph_modeling"

    # ========================================================================
    # Pattern 3: Tool Unloading
    # ========================================================================

    @pytest.mark.asyncio
    async def test_advance_workflow_stage_valid(self):
        """Test arango_advance_workflow_stage with valid stage."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_ADVANCE_WORKFLOW_STAGE,
                {"stage": "data_loading"}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert "from_stage" in response_data
            assert "to_stage" in response_data
            assert response_data["to_stage"] == "data_loading"
            assert "description" in response_data
            assert "tools_unloaded" in response_data
            assert "tools_loaded" in response_data
            assert "active_tools" in response_data

    @pytest.mark.asyncio
    async def test_advance_workflow_stage_invalid(self):
        """Test arango_advance_workflow_stage with invalid stage."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_ADVANCE_WORKFLOW_STAGE,
                {"stage": "invalid_stage"}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            # Pydantic validation error occurs before handler is called
            assert "error" in response_data
            assert response_data["error"] == "ValidationError"

    @pytest.mark.asyncio
    async def test_workflow_stage_progression(self):
        """Test complete workflow stage progression."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            # Reset to setup stage
            await server._handlers["call_tool"](
                ARANGO_ADVANCE_WORKFLOW_STAGE,
                {"stage": "setup"}
            )

            # Progress through stages
            stages = ["data_loading", "analysis", "cleanup"]
            previous_stage = "setup"

            for stage in stages:
                result = await server._handlers["call_tool"](
                    ARANGO_ADVANCE_WORKFLOW_STAGE,
                    {"stage": stage}
                )

                data = json.loads(result[0].text)
                assert data["from_stage"] == previous_stage
                assert data["to_stage"] == stage
                previous_stage = stage

    @pytest.mark.asyncio
    async def test_get_tool_usage_stats(self):
        """Test arango_get_tool_usage_stats through MCP server."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_GET_TOOL_USAGE_STATS,
                {}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert "current_stage" in response_data
            assert "tool_usage" in response_data
            assert "total_tools_used" in response_data
            assert "active_stage_tools" in response_data

    @pytest.mark.asyncio
    async def test_unload_tools_valid(self):
        """Test arango_unload_tools with valid tool names."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_UNLOAD_TOOLS,
                {"tool_names": ["arango_query", "arango_insert"]}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert "unloaded" in response_data
            assert "not_found" in response_data
            assert "total_unloaded" in response_data
            assert "arango_query" in response_data["unloaded"]
            assert "arango_insert" in response_data["unloaded"]

    @pytest.mark.asyncio
    async def test_unload_tools_invalid(self):
        """Test arango_unload_tools with invalid tool names."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            result = await server._handlers["call_tool"](
                ARANGO_UNLOAD_TOOLS,
                {"tool_names": ["invalid_tool_1", "invalid_tool_2"]}
            )

            assert len(result) == 1
            response_data = json.loads(result[0].text)

            assert len(response_data["not_found"]) == 2
            assert response_data["total_unloaded"] == 0

    # ========================================================================
    # End-to-End Workflow Testing
    # ========================================================================

    @pytest.mark.asyncio
    async def test_complete_mcp_design_pattern_workflow(self):
        """Test realistic workflow combining all three patterns."""
        with patch.object(server, 'request_context') as mock_ctx:
            mock_ctx.lifespan_context = {"db": self.mock_db, "client": self.mock_client}

            # Step 1: Search for tools (Pattern 1)
            search_result = await server._handlers["call_tool"](
                ARANGO_SEARCH_TOOLS,
                {
                    "keywords": ["graph"],
                    "categories": ["graph_basic"],
                    "detail_level": "summary"
                }
            )
            search_data = json.loads(search_result[0].text)
            assert search_data["total_matches"] > 0

            # Step 2: Switch to graph_modeling context (Pattern 2)
            switch_result = await server._handlers["call_tool"](
                ARANGO_SWITCH_CONTEXT,
                {"context": "graph_modeling"}
            )
            switch_data = json.loads(switch_result[0].text)
            assert switch_data["to_context"] == "graph_modeling"

            # Step 3: Advance to setup stage (Pattern 3)
            stage_result = await server._handlers["call_tool"](
                ARANGO_ADVANCE_WORKFLOW_STAGE,
                {"stage": "setup"}
            )
            stage_data = json.loads(stage_result[0].text)
            assert stage_data["to_stage"] == "setup"

            # Step 4: Verify active context
            context_result = await server._handlers["call_tool"](
                ARANGO_GET_ACTIVE_CONTEXT,
                {}
            )
            context_data = json.loads(context_result[0].text)
            assert context_data["active_context"] == "graph_modeling"

            # Step 5: Get tool usage stats
            stats_result = await server._handlers["call_tool"](
                ARANGO_GET_TOOL_USAGE_STATS,
                {}
            )
            stats_data = json.loads(stats_result[0].text)
            assert stats_data["current_stage"] == "setup"

    @pytest.mark.asyncio
    async def test_mcp_design_pattern_tools_in_full_toolset(self):
        """Verify all 9 MCP Design Pattern tools are available in full toolset."""
        with patch.dict('os.environ', {'MCP_COMPAT_TOOLSET': 'full'}):
            tools = await server._handlers["list_tools"]()
            tool_names = [tool.name for tool in tools]

            # Verify all 9 new tools are present
            expected_tools = [
                ARANGO_SEARCH_TOOLS,
                ARANGO_LIST_TOOLS_BY_CATEGORY,
                ARANGO_SWITCH_CONTEXT,
                ARANGO_GET_ACTIVE_CONTEXT,
                ARANGO_LIST_CONTEXTS,
                ARANGO_ADVANCE_WORKFLOW_STAGE,
                ARANGO_GET_TOOL_USAGE_STATS,
                ARANGO_UNLOAD_TOOLS,
            ]

            for tool in expected_tools:
                assert tool in tool_names, f"MCP Design Pattern tool {tool} not found in tool list"
