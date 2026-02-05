"""Handler dispatcher for arango_admin_optimize."""

from __future__ import annotations

from typing import Any, Dict

from arango.database import StandardDatabase

from .operations import optimize_edges_from_logs, quality_check_edges

OPERATIONS = {
    "run": optimize_edges_from_logs,
    "quality_check": quality_check_edges,
}


def handle_admin_optimize(
    db: StandardDatabase, action: str, args: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Dispatch admin optimize operation."""
    if action not in OPERATIONS:
        return {"error": f"Unknown admin_optimize action: {action}"}

    handler = OPERATIONS[action]
    try:
        return handler(db, args or {})
    except Exception as exc:
        return {"error": str(exc), "action": action}
