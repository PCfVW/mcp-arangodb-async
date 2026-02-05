"""Unified dispatcher for arango_admin.

Consolidates previously separate tool entrances:
- arango_aql
- arango_template
- arango_admin_sync
- arango_admin_optimize
"""

from __future__ import annotations

from typing import Any, Dict

from arango.database import StandardDatabase

from ..aql.handler import handle_aql
from ..template.handler import handle_template
from .sync.handler import handle_admin_sync
from .optimize.handler import handle_admin_optimize


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

    if action == "sync_run":
        return handle_admin_sync(db, "run", args)

    if action == "optimize_run":
        return handle_admin_optimize(db, "run", args)

    if action == "quality_check":
        return handle_admin_optimize(db, "quality_check", args)

    return {"error": f"Unknown admin action: {action}"}
