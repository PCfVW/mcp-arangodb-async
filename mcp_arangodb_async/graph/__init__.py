"""Graph operations module.

Provides graph management, traversal, backup/restore, and analysis operations.

Operations:
    Management:
        - create: Create a named graph
        - list: List available graphs
        - add_vertex_collection: Add vertex collection to graph
        - add_edge_definition: Create edge definition in graph

    Edge:
        - add_edge: Insert edge document

    Traversal:
        - traverse: Perform bounded graph traversal
        - shortest_path: Compute shortest path between vertices

    Backup:
        - backup: Export graph structure
        - restore: Import graph data
        - backup_named: Backup graph definitions

    Analysis:
        - validate_integrity: Verify graph consistency
        - statistics: Generate graph analytics
"""

from .handler import handle_graph, OPERATIONS

__all__ = ["handle_graph", "OPERATIONS"]
