"""Unified dispatcher for admin optimize operations.

Routes four actions to their operation modules:
- sync_run     -> sync.py
- optimize_run -> edges.py
- quality_check -> quality.py
- embedding_run -> embedding.py (generate/search/status via sub_action)
"""

from __future__ import annotations

from typing import Any, Dict

from arango.database import StandardDatabase

from .sync import sync_tags_and_edges
from .edges import optimize_edges_from_logs
from .quality import quality_check_edges
from .embedding import embedding_generate, embedding_search, embedding_status

OPERATIONS = {
    "sync_run": sync_tags_and_edges,
    "optimize_run": optimize_edges_from_logs,
    "quality_check": quality_check_edges,
}

EMBEDDING_SUB_ACTIONS = {
    "generate": embedding_generate,
    "search": embedding_search,
    "status": embedding_status,
}


def handle_admin_optimize(
    db: StandardDatabase, action: str, args: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Dispatch admin optimize operation."""
    args = args or {}

    # Direct action dispatch (sync_run, optimize_run, quality_check)
    op_fn = OPERATIONS.get(action)
    if op_fn is not None:
        try:
            return op_fn(db, args)
        except Exception as exc:
            return {"error": str(exc), "action": action}

    # Embedding sub-action dispatch
    if action == "embedding_run":
        sub_action = args.get("embedding_action", "status")
        sub_fn = EMBEDDING_SUB_ACTIONS.get(sub_action)
        if sub_fn is None:
            return {
                "error": f"Unknown embedding_action: {sub_action}",
                "available": list(EMBEDDING_SUB_ACTIONS.keys()),
            }
        try:
            return sub_fn(db, args)
        except Exception as exc:
            return {"error": str(exc), "action": action, "embedding_action": sub_action}

    return {
        "error": f"Unknown optimize action: {action}",
        "available": list(OPERATIONS.keys()) + ["embedding_run"],
    }
