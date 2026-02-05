"""Graph management operations."""

from __future__ import annotations

from typing import Any, Dict, List
from arango.database import StandardDatabase


def create_graph(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a named graph with edge definitions, optionally creating collections."""
    """
    Operator model:
      Preconditions:
        - Database connection available.
        - 'name' provided; 'edge_definitions' well-formed with edge/from/to collections.
      Effects:
        - Optionally creates required vertex/edge collections.
        - Creates the graph if missing; returns summary info.
        - Mutates database when creating collections/graph.
    """
    name = args["name"]
    edge_defs = args.get("edge_definitions") or []
    create_colls = bool(args.get("create_collections", True))

    # Prepare edge definitions for python-arango
    arango_edge_defs: List[Dict[str, Any]] = []
    for ed in edge_defs:
        arango_edge_defs.append(
            {
                "edge_collection": ed["edge_collection"],
                "from_vertex_collections": ed["from_collections"],
                "to_vertex_collections": ed["to_collections"],
            }
        )

    # Create vertex and edge collections if requested
    if create_colls:
        for ed in edge_defs:
            if not db.has_collection(ed["edge_collection"]):
                db.create_collection(ed["edge_collection"], edge=True)
            for vc in ed["from_collections"] + ed["to_collections"]:
                if not db.has_collection(vc):
                    db.create_collection(vc, edge=False)

    # Create or get graph
    if not db.has_graph(name):
        g = db.create_graph(name, edge_definitions=arango_edge_defs)
    else:
        g = db.graph(name)

    # Return summary
    info = {
        "name": name,
        "edge_definitions": edge_defs,
        "vertex_collections": sorted(
            {
                vc
                for ed in edge_defs
                for vc in (ed["from_collections"] + ed["to_collections"])
            }
        ),
    }
    return info


def list_graphs(
    db: StandardDatabase, args: Dict[str, Any] | None = None
) -> List[Dict[str, Any]]:
    """List available graphs in the database.

    Returns a simplified list of graph metadata with at least the name.

    Operator model:
      Preconditions:
        - Database connection available.
      Effects:
        - Reads and returns graph metadata (name, and raw if available).
        - No database mutations.
    """
    try:
        graphs = db.graphs()  # type: ignore[attr-defined]
    except Exception:
        graphs = []
    result: List[Dict[str, Any]] = []
    for g in graphs or []:
        # Support both dict and object-like items
        if isinstance(g, dict):
            result.append(
                {
                    "name": g.get("name"),
                    "_raw": g,
                }
            )
        else:
            name = getattr(g, "name", None)
            result.append({"name": name})
    return result


def add_vertex_collection(
    db: StandardDatabase, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Add a vertex collection to a named graph."""
    """
    Operator model:
      Preconditions:
        - Database connection available; graph exists; collection exists.
      Effects:
        - Adds the vertex collection to the graph.
        - Mutates the graph definition.
    """
    graph_name = args["graph"]
    collection = args["collection"]
    g = db.graph(graph_name)
    g.add_vertex_collection(collection)  # type: ignore[attr-defined]
    return {"graph": graph_name, "collection_added": collection}


def add_edge_definition(
    db: StandardDatabase, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Create an edge definition in a named graph."""
    """
    Operator model:
      Preconditions:
        - Database connection available; graph exists; edge and vertex collections exist.
      Effects:
        - Creates the edge definition on the graph.
        - Mutates the graph definition.
    """
    graph_name = args["graph"]
    edge_collection = args["edge_collection"]
    from_cols = args.get("from_collections") or []
    to_cols = args.get("to_collections") or []
    g = db.graph(graph_name)
    g.create_edge_definition(  # type: ignore[attr-defined]
        edge_collection=edge_collection,
        from_vertex_collections=from_cols,
        to_vertex_collections=to_cols,
    )
    return {
        "graph": graph_name,
        "edge_definition": {
            "edge_collection": edge_collection,
            "from_collections": from_cols,
            "to_collections": to_cols,
        },
    }
