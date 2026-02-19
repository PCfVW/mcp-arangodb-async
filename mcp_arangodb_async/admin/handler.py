"""Unified dispatcher for arango_admin.

Consolidates previously separate tool entrances:
- arango_aql
- arango_template
- arango_admin_optimize (sync, optimize, quality_check, embedding)
"""

from __future__ import annotations

from functools import partial
from typing import Any, Dict

from arango.database import StandardDatabase

from ..aql.handler import handle_aql
from ..template.handler import handle_template
from .optimize.handler import handle_admin_optimize
from ..utility.runtime_defaults import get_available_actions


def _aql(aql_action: str, db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    return handle_aql(db, aql_action, args)


OPERATIONS: Dict[str, Any] = {
    "aql_query":        partial(_aql, "query"),
    "aql_explain":      partial(_aql, "explain"),
    "aql_profile":      partial(_aql, "profile"),
    "aql_build":        partial(_aql, "build"),
    "template_execute": lambda db, args: handle_template(db, args),
    "sync_run":         lambda db, args: handle_admin_optimize(db, "sync_run", args),
    "optimize_run":     lambda db, args: handle_admin_optimize(db, "optimize_run", args),
    "quality_check":    lambda db, args: handle_admin_optimize(db, "quality_check", args),
    "embedding_run":    lambda db, args: handle_admin_optimize(db, "embedding_run", args),
}


def handle_admin(
    db: StandardDatabase, action: str, args: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Dispatch admin action to the appropriate internal module."""
    args = args or {}

    if action not in OPERATIONS:
        available = get_available_actions("arango_admin")
        return {
            "error": f"Unknown action: {action}",
            "tool": "arango_admin",
            "available_actions": available,
            "hint": f"Use one of: {', '.join(available)}"
        }

    return OPERATIONS[action](db, args)
