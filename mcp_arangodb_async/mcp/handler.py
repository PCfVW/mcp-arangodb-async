"""MCP metadata tool handler dispatcher.

Maps operation names to metadata operation functions.
"""

from typing import Any, Dict
from arango.database import StandardDatabase

from . import metadata
from ..utility.runtime_defaults import get_available_actions


OPERATIONS = {
    "search_tools": metadata.search_tools,
    "list_by_category": metadata.list_tools_by_category,
    "get_workflow": metadata.get_active_workflow,
    "list_workflows": metadata.list_workflows,
    "usage_stats": metadata.get_tool_usage_stats,
    "unload": metadata.unload_tools,
}


def handle_mcp(
    db: StandardDatabase, action: str, args: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Dispatch MCP metadata operations to appropriate handler.

    Args:
        db: ArangoDB database instance (may be unused for metadata operations)
        action: Operation name (e.g., 'search_tools', 'list_by_category', 'usage_stats')
        args: Operation arguments (optional)

    Returns:
        Operation result or error dictionary
    """
    if action not in OPERATIONS:
        available = get_available_actions("arango_mcp")
        return {
            "error": f"Unknown action: {action}",
            "tool": "arango_mcp",
            "available_actions": available,
            "hint": f"Use one of: {', '.join(available)}"
        }

    handler = OPERATIONS[action]

    try:
        if args is None:
            # For parameter-less operations
            return handler(db)
        else:
            return handler(db, args)
    except Exception as e:
        return {"error": str(e), "action": action}
