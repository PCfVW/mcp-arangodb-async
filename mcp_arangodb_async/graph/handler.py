"""Graph tool handler with operation dispatch."""

from __future__ import annotations

from typing import Any, Dict
from arango.database import StandardDatabase

from . import management, edge, traversal, graph_backup, analysis


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


def handle_graph(db: StandardDatabase, operation: str, args: Dict[str, Any]) -> Any:
    """Dispatch graph operations to appropriate handler functions.

    Args:
        db: ArangoDB database instance
        operation: Operation name from OPERATIONS dict
        args: Operation arguments

    Returns:
        Operation result

    Raises:
        ValueError: If operation not found
    """
    if operation not in OPERATIONS:
        raise ValueError(f"Unknown graph operation: {operation}")

    handler = OPERATIONS[operation]
    return handler(db, args)
