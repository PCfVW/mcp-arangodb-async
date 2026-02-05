"""V4 Test Suite for ArangoDB MCP Server.

This package contains comprehensive unit tests for all v4 tools:
- test_database_v4: Database operations (4 operations)
- test_collection_v4: Collection operations (23 operations)
- test_view_v4: View operations (6 operations)
- test_graph_v4: Graph operations (12 operations)
- test_aql_v4: AQL operations (4 operations)
- test_mcp_v4: MCP metadata operations (6 operations)

Total: 55 operations covered by tests using TDD approach with mocked dependencies.
"""

__version__ = "1.0.0"  # v4-refactor branch
__all__ = [
    "test_database_v4",
    "test_collection_v4",
    "test_view_v4",
    "test_graph_v4",
    "test_aql_v4",
    "test_mcp_v4",
]
