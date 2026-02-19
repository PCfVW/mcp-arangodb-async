"""Graph tool handler with operation dispatch."""

from __future__ import annotations

from typing import Any, Dict
from arango.database import StandardDatabase

from . import management, edge, traversal, graph_backup, analysis
from ..utility.runtime_defaults import get_available_actions


OPERATIONS = {
    # Management (management.py)
    "create": management.create_graph,
    "list": management.list_graphs,
    "add_vertex_collection": management.add_vertex_collection,
    "add_edge_definition": management.add_edge_definition,

    # Edge (edge.py)
    "add_edge": edge.add_edge,

    # Traversal (traversal.py)
    "traverse": traversal.traverse,
    "shortest_path": traversal.shortest_path,

    # Backup (graph_backup.py)
    "backup": graph_backup.backup_graph,
    "restore": graph_backup.restore_graph,
    "backup_named": graph_backup.backup_named_graphs,

    # Analysis (analysis.py)
    "validate_integrity": analysis.validate_graph_integrity,
    "statistics": analysis.graph_statistics,
}


def handle_graph(db: StandardDatabase, action: str, args: Dict[str, Any]) -> Any:
    """Dispatch graph operations to appropriate handler functions.

    Args:
        db: ArangoDB database instance
        action: Action name from OPERATIONS dict
        args: Operation arguments

    Returns:
        Operation result or error dictionary
    """
    if action not in OPERATIONS:
        available = get_available_actions("arango_graph")
        return {
            "error": f"Unknown action: {action}",
            "tool": "arango_graph",
            "available_actions": available,
            "hint": f"Use one of: {', '.join(available)}"
        }

    handler = OPERATIONS[action]
    try:
        return handler(db, args)
    except Exception as e:
        return {"error": str(e), "action": action}
