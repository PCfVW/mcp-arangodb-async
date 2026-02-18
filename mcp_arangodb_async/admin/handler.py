"""Unified dispatcher for arango_admin.

Consolidates previously separate tool entrances:
- arango_aql
- arango_template
- arango_admin_optimize (sync, optimize, quality_check, embedding)
"""

from __future__ import annotations

from typing import Any, Dict

from arango.database import StandardDatabase

from ..aql.handler import handle_aql
from ..template.handler import handle_template
from .optimize.handler import handle_admin_optimize
from ..utility.runtime_defaults import get_available_actions


def handle_admin(
    db: StandardDatabase, action: str, args: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Dispatch admin action to the appropriate internal module."""
    args = args or {}

    if action == "aql_query":
        return handle_aql(db, "query", args)
    if action == "aql_explain":
        return handle_aql(db, "explain", args)
    if action == "aql_profile":
        return handle_aql(db, "profile", args)
    if action == "aql_build":
        return handle_aql(db, "build", args)

    if action == "template_execute":
        return handle_template(db, args)

    if action in ("sync_run", "optimize_run", "quality_check", "embedding_run"):
        return handle_admin_optimize(db, action, args)

    available = get_available_actions("arango_admin")
    return {
        "error": f"Unknown action: {action}",
        "tool": "arango_admin",
        "available_actions": available,
        "hint": f"Use one of: {', '.join(available)}"
    }
