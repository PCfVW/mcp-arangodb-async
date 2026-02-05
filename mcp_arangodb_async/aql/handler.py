"""AQL tool handler dispatcher for mcp-arango-mind v4.0."""

from typing import Any, Dict
from arango.database import StandardDatabase

from . import query
from . import builder

OPERATIONS = {
    # Query (query.py)
    "query": query.arango_query,
    "explain": query.explain_query,
    "profile": query.query_profile,
    # Builder (builder.py)
    "build": builder.query_builder,
}


def handle_aql(
    db: StandardDatabase, action: str, args: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Dispatch AQL operations to appropriate handler.

    Args:
        db: ArangoDB database instance
        action: Operation name (e.g., 'query', 'explain', 'profile', 'build')
        args: Operation arguments (optional for parameter-less operations)

    Returns:
        Operation result or error dictionary
    """
    if action not in OPERATIONS:
        return {"error": f"Unknown AQL action: {action}"}

    handler = OPERATIONS[action]

    try:
        if args is None:
            # For parameter-less operations
            return handler(db)
        else:
            return handler(db, args)
    except Exception as e:
        return {"error": str(e), "action": action}
