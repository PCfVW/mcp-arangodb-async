"""Handler dispatcher for arango_admin_sync."""

from __future__ import annotations

from typing import Any, Dict

from arango.database import StandardDatabase

from .operations import sync_tags_and_edges

OPERATIONS = {
    "run": sync_tags_and_edges,
}


def handle_admin_sync(
    db: StandardDatabase, action: str, args: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Dispatch admin sync operation."""
    if action not in OPERATIONS:
        return {"error": f"Unknown admin_sync action: {action}"}

    handler = OPERATIONS[action]
    try:
        return handler(db, args or {})
    except Exception as exc:
        return {"error": str(exc), "action": action}
