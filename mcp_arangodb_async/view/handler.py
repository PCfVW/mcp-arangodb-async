"""ArangoSearch view handler - dispatches view operations."""

from typing import Any, Dict
from arango.database import StandardDatabase

from . import operations
from ..utility.runtime_defaults import get_available_actions

OPERATIONS = {
    # View management
    "create": operations.create_view,
    "drop": operations.drop_view,
    "list": operations.list_views,
    "get": operations.get_view,
    "update": operations.update_view,
    # Search
    "search": operations.search_view,
}


def handle_view(
    db: StandardDatabase, action: str, args: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Dispatch view operations to appropriate handler.

    Args:
        db: ArangoDB database instance
        action: Operation name (e.g., 'create', 'drop', 'list', 'search')
        args: Operation arguments (optional for parameter-less operations like 'list')

    Returns:
        Operation result or error dictionary
    """
    if action not in OPERATIONS:
        available = get_available_actions("arango_view")
        return {
            "error": f"Unknown action: {action}",
            "tool": "arango_view",
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
