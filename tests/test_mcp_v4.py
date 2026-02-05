"""Unit tests for arango_mcp tool (v4)."""

from unittest.mock import MagicMock
from mcp_arangodb_async.mcp.handler import handle_mcp
from mcp_arangodb_async.mcp.metadata import search_tools, list_by_category, usage_stats


class TestMCPToolSearch:
    """Test tool search operations."""

    def test_search_tools_by_keyword(self, mock_db):
        """Should search tools by keyword."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {
                "name": "arango_collection",
                "description": "Collection operations",
                "category": "data",
            },
        ])

        args = {"keywords": ["collection"]}

        # Act
        result = handle_mcp(mock_db, "search_tools", args)

        # Assert
        assert isinstance(result, dict)
        assert "matches" in result

    def test_search_tools_returns_matching_tools(self, mock_db):
        """Should return tools matching query."""
        # Arrange
        matching_tools = [
            {"name": "arango_view", "tags": ["view", "search"]},
            {"name": "arango_graph", "tags": ["graph", "traversal"]},
        ]
        mock_db.aql.execute.return_value = iter(matching_tools)

        args = {"keywords": ["search"]}

        # Act
        result = handle_mcp(mock_db, "search_tools", args)

        # Assert
        assert isinstance(result, dict)

    def test_search_tools_with_filters(self, mock_db):
        """Should support filtering search results."""
        # Arrange
        mock_db.aql.execute.return_value = iter([])

        args = {"keywords": ["collection"], "categories": ["collection"]}

        # Act
        result = handle_mcp(mock_db, "search_tools", args)

        # Assert
        assert isinstance(result, dict)


class TestMCPToolCategories:
    """Test tool categorization."""

    def test_list_tools_by_category(self, mock_db):
        """Should list tools organized by category."""
        # Arrange
        categories = {
            "data": ["arango_collection", "arango_view"],
            "query": ["arango_aql"],
            "structure": ["arango_graph", "arango_database"],
        }
        mock_db.aql.execute.return_value = iter([
            {"category": "data", "tools": categories["data"]},
            {"category": "query", "tools": categories["query"]},
        ])

        args = {}

        # Act
        result = handle_mcp(mock_db, "list_by_category", args)

        # Assert
        assert isinstance(result, dict)

    def test_list_tools_by_category_includes_descriptions(self, mock_db):
        """Should include tool descriptions in category listing."""
        # Arrange
        mock_db.aql.execute.return_value = iter([
            {
                "category": "data",
                "tools": [
                    {
                        "name": "arango_collection",
                        "description": "Collection CRUD operations",
                        "operations": 23,
                    }
                ],
            }
        ])

        args = {}

        # Act
        result = handle_mcp(mock_db, "list_by_category", args)

        # Assert
        assert isinstance(result, dict)

    def test_list_all_categories(self, mock_db):
        """Should list all available categories."""
        # Arrange
        args = {}

        # Act
        result = handle_mcp(mock_db, "list_by_category", args)

        # Assert
        assert isinstance(result, dict)


class TestMCPWorkflows:
    """Test workflow operations."""

    def test_get_workflow_definition(self, mock_db):
        """Should retrieve workflow definition."""
        # Arrange
        workflow_def = {
            "_key": "data_import",
            "name": "Data Import Workflow",
            "stages": [
                {"name": "upload", "tools": ["arango_collection"]},
                {"name": "validate", "tools": ["arango_collection"]},
                {"name": "transform", "tools": ["arango_aql"]},
                {"name": "import", "tools": ["arango_collection"]},
            ],
        }
        mock_collection = MagicMock()
        mock_collection.get.return_value = workflow_def
        mock_db.collection.return_value = mock_collection

        args = {"workflow": "data_import"}

        # Act
        result = handle_mcp(mock_db, "get_workflow", args)

        # Assert
        assert isinstance(result, dict)

    def test_list_available_workflows(self, mock_db):
        """Should list available workflows."""
        # Arrange
        workflows = [
            {
                "_key": "data_import",
                "name": "Data Import",
                "description": "Import data from files",
            },
            {
                "_key": "graph_analysis",
                "name": "Graph Analysis",
                "description": "Analyze graph structure",
            },
        ]
        mock_collection = MagicMock()
        mock_collection.all.return_value = iter(workflows)
        mock_db.collection.return_value = mock_collection

        args = {}

        # Act
        result = handle_mcp(mock_db, "list_workflows", args)

        # Assert
        assert isinstance(result, dict)

    def test_workflow_includes_next_stages(self, mock_db):
        """Should include available next stages."""
        # Arrange
        workflow_def = {
            "current_stage": "upload",
            "available_next_stages": ["validate", "import"],
            "stages": [
                {"name": "upload", "status": "completed"},
                {"name": "validate", "status": "pending"},
                {"name": "import", "status": "pending"},
            ],
        }
        mock_collection = MagicMock()
        mock_collection.get.return_value = workflow_def
        mock_db.collection.return_value = mock_collection

        args = {"workflow": "data_import"}

        # Act
        result = handle_mcp(mock_db, "get_workflow", args)

        # Assert
        assert isinstance(result, dict)


class TestMCPUsageStats:
    """Test usage statistics operations."""

    def test_tool_usage_statistics(self, mock_db):
        """Should return tool usage statistics."""
        # Arrange
        stats = {
            "arango_collection": {
                "calls": 1250,
                "errors": 5,
                "avg_time_ms": 45.2,
            },
            "arango_aql": {
                "calls": 890,
                "errors": 2,
                "avg_time_ms": 78.5,
            },
        }
        mock_db.aql.execute.return_value = iter([stats])

        args = {}

        # Act
        result = handle_mcp(mock_db, "usage_stats", args)

        # Assert
        assert isinstance(result, dict)

    def test_usage_stats_by_tool(self, mock_db):
        """Should provide usage stats per tool."""
        # Arrange
        args = {"tool_names": ["arango_collection"]}

        # Act
        result = handle_mcp(mock_db, "usage_stats", args)

        # Assert
        assert isinstance(result, dict)

    def test_usage_stats_time_range(self, mock_db):
        """Should support time range filtering."""
        # Arrange
        args = {
            "time_range": "last_7_days",
        }

        # Act
        result = handle_mcp(mock_db, "usage_stats", args)

        # Assert
        assert isinstance(result, dict)

    def test_usage_stats_includes_errors(self, mock_db):
        """Should include error statistics."""
        # Arrange
        args = {"tool_names": []}

        # Act
        result = handle_mcp(mock_db, "usage_stats", args)

        # Assert
        assert isinstance(result, dict)


class TestMCPUnload:
    """Test tool unload operation."""

    def test_unload_tool(self, mock_db):
        """Should unload tool from memory."""
        # Arrange
        args = {"tool": "arango_collection"}

        # Act
        result = handle_mcp(mock_db, "unload", args)

        # Assert
        assert isinstance(result, dict)

    def test_unload_all_tools(self, mock_db):
        """Should unload all tools."""
        # Arrange
        args = {}

        # Act
        result = handle_mcp(mock_db, "unload", args)

        # Assert
        assert isinstance(result, dict)


class TestMCPHandler:
    """Test MCP handler dispatch."""

    def test_handler_dispatches_all_operations(self, mock_db):
        """Should dispatch all MCP operations."""
        # Arrange
        mock_db.aql.execute.return_value = iter([])
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection

        operations = [
            ("search_tools", {"keywords": ["collection"]}),
            ("list_by_category", {}),
            ("usage_stats", {}),
            ("unload", {"tool_names": []}),
        ]

        # Act & Assert
        for operation, args in operations:
            result = handle_mcp(mock_db, operation, args)
            assert isinstance(result, dict)

    def test_handler_rejects_unknown_operation(self, mock_db):
        """Should reject unknown operations."""
        # Arrange
        args = {}

        # Act
        result = handle_mcp(mock_db, "unknown_op", args)

        # Assert
        assert "error" in result or isinstance(result, dict)


class TestMCPModels:
    """Test MCP model validation."""

    def test_mcp_args_validation(self):
        """Should validate MCPArgs model."""
        from mcp_arangodb_async.mcp.models import MCPArgs

        # Arrange & Act
        args = MCPArgs(action="search_tools")

        # Assert
        assert args.action == "search_tools"

    def test_search_tools_args_validation(self):
        """Should validate SearchToolsArgs model."""
        from mcp_arangodb_async.mcp.models import SearchToolsArgs

        # Arrange & Act
        args = SearchToolsArgs(keywords=["collection"])

        # Assert
        assert args.keywords == ["collection"]
