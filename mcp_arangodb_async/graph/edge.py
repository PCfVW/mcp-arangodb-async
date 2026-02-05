"""Graph edge operations."""

from __future__ import annotations

from typing import Any, Dict
from arango.database import StandardDatabase


def add_edge(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Insert an edge document with _from and _to and optional attributes."""
    """
    Operator model:
      Preconditions:
        - Database connection available; edge collection exists.
        - '_from' and '_to' target vertices exist or are acceptable by DB constraints.
      Effects:
        - Inserts edge document; returns metadata.
        - Mutates the edge collection.
    """
    col = db.collection(args["collection"])
    payload = {
        "_from": args["from_id"],
        "_to": args["to_id"],
        **(args.get("attributes") or {}),
    }
    result = col.insert(payload)
    return {
        "_id": result.get("_id"),
        "_key": result.get("_key"),
        "_rev": result.get("_rev"),
    }
