"""Graph traversal operations."""

from __future__ import annotations

from typing import Any, Dict, List
from contextlib import contextmanager
from arango.database import StandardDatabase


@contextmanager
def safe_cursor(cursor):
    """Context manager for safe cursor handling."""
    try:
        yield cursor
    finally:
        if hasattr(cursor, 'close'):
            cursor.close()


def traverse(db: StandardDatabase, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Perform a bounded traversal via AQL using either a named graph or edge collections."""
    """
    Operator model:
      Preconditions:
        - Database connection available.
        - Either 'graph' is provided or 'edge_collections' is a non-empty list.
        - 'start_vertex' provided; optional bounds and options valid.
      Effects:
        - Executes traversal query; returns paths or vertex/edge pairs.
        - No database mutations.
    """
    start = args["start_vertex"]
    direction = args.get("direction", "OUTBOUND")
    min_depth = int(args.get("min_depth", 1))
    max_depth = int(args.get("max_depth", 1))
    graph = args.get("graph")
    edge_cols = args.get("edge_collections") or []
    return_paths = bool(args.get("return_paths", False))
    limit = args.get("limit")

    if graph:
        aql = f"""
        FOR v, e, p IN {min_depth}..{max_depth} {direction} @start GRAPH @graph
          {"LIMIT @limit" if limit else ""}
          RETURN {"p" if return_paths else "{ vertex: v, edge: e }"}
        """
        bind = {"start": start, "graph": graph}
    else:
        if not edge_cols:
            raise ValueError(
                "edge_collections must be provided when graph is not specified"
            )
        # Traversal over explicit edge collections (comma-separated list)
        edge_expr = ", ".join(edge_cols)
        aql = f"""
        FOR v, e, p IN {min_depth}..{max_depth} {direction} @start {edge_expr}
          {"LIMIT @limit" if limit else ""}
          RETURN {"p" if return_paths else "{ vertex: v, edge: e }"}
        """
        bind = {"start": start}

    if limit:
        bind["limit"] = int(limit)
    cursor = db.aql.execute(aql, bind_vars=bind)
    with safe_cursor(cursor):
        return list(cursor)


def shortest_path(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Compute shortest path between two vertices using AQL."""
    """
    Operator model:
      Preconditions:
        - Database connection available.
        - 'start_vertex' and 'end_vertex' provided; either 'graph' or 'edge_collections' provided.
      Effects:
        - Executes shortest path query; returns found=False or the path.
        - No database mutations.
    """
    start = args["start_vertex"]
    end = args["end_vertex"]
    direction = args.get("direction", "OUTBOUND")
    graph = args.get("graph")
    edge_cols = args.get("edge_collections") or []
    return_paths = bool(args.get("return_paths", True))

    if graph:
        aql = f"""
        FOR v, e IN {direction} SHORTEST_PATH @start TO @end GRAPH @graph
          RETURN {{ vertices: v, edges: e }}
        """
        bind = {"start": start, "end": end, "graph": graph}
    else:
        if not edge_cols:
            raise ValueError(
                "edge_collections must be provided when graph is not specified"
            )
        edge_expr = ", ".join(edge_cols)
        aql = f"""
        FOR v, e IN {direction} SHORTEST_PATH @start TO @end {edge_expr}
          RETURN {{ vertices: v, edges: e }}
        """
        bind = {"start": start, "end": end}

    cursor = db.aql.execute(aql, bind_vars=bind)
    with safe_cursor(cursor):
        paths = list(cursor)
    if not paths:
        return {"found": False}
    # AQL returns a single element containing arrays of vertices/edges along the path
    res = paths[0]
    return {"found": True, **res}
