"""AQL query operations for ArangoDB."""

from __future__ import annotations

from typing import Any, Dict, List
from contextlib import contextmanager
from arango.database import StandardDatabase

from ..utility.access_log import log_query_results, ACCESS_TYPE_QUERY


@contextmanager
def safe_cursor(cursor):
    """Context manager for safe cursor handling."""
    try:
        yield cursor
    finally:
        if hasattr(cursor, "close"):
            try:
                cursor.close()
            except Exception:
                pass  # Ignore cleanup errors


def arango_query(
    db: StandardDatabase, args: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Execute an AQL query with optional bind vars and return the result list.

    This mirrors the TS tool `arango_query` behavior at a high level.

    Operator model:
      Preconditions:
        - Database connection available.
        - Args include 'query' (str); optional 'bind_vars' (object).
      Effects:
        - Executes AQL query and returns list of rows.
        - No database mutations unless the query itself is a write.
    """
    cursor = db.aql.execute(args["query"], bind_vars=args.get("bind_vars") or {})
    with safe_cursor(cursor):
        results = list(cursor)
        # Log access
        log_query_results(db, results, ACCESS_TYPE_QUERY)
        return results


def explain_query(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze query execution plan and optionally include index suggestions."""
    """
    Operator model:
      Preconditions:
        - Database connection available.
        - Args include 'query' (str); optional 'bind_vars' (object), 'max_plans' (int), 'suggest_indexes' (bool).
      Effects:
        - Calls AQL explain and returns {plans, warnings, stats, index_suggestions?}.
        - No database mutations are performed.
    """
    explain = db.aql.explain(
        args["query"],
        bind_vars=args.get("bind_vars") or {},
        max_plans=int(args.get("max_plans", 1)),
    )
    result: Dict[str, Any] = {
        "plans": explain.get("plans") or [],
        "warnings": explain.get("warnings") or [],
        "stats": explain.get("stats") or {},
    }
    if args.get("suggest_indexes", True):
        result["index_suggestions"] = _analyze_query_for_indexes(
            args["query"], result["plans"]
        )  # best-effort
    return result


def _analyze_query_for_indexes(
    query: str, plans: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Heuristic index suggestions based on execution nodes."""
    suggestions: List[Dict[str, Any]] = []
    for plan in plans or []:
        for node in plan.get("nodes", []):
            node_type = node.get("type")
            # Suggest on Filter / IndexNode absence
            if node_type == "Filter" or node_type == "EnumerateCollection":
                # Basic hint without deep AQL parsing
                suggestions.append(
                    {
                        "hint": "Consider adding a persistent/hash index for filtered fields",
                        "nodeId": node.get("id"),
                    }
                )
    # Deduplicate hints
    unique = []
    seen = set()
    for s in suggestions:
        key = (s.get("hint"), s.get("nodeId"))
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


def query_profile(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Return explain plans and stats for a query (profiling helper).

    Operator model:
      Preconditions:
        - Database connection available.
        - Args include 'query' (str); optional 'bind_vars' (object) and 'max_plans' (int).
      Effects:
        - Calls AQL explain on the provided query/bind vars.
        - Returns {plans, warnings, stats} for profiling/analysis.
        - No database mutations are performed.
    """
    explain = db.aql.explain(
        args["query"],
        bind_vars=args.get("bind_vars") or {},
        max_plans=int(args.get("max_plans", 1)),
    )
    return {
        "plans": explain.get("plans") or [],
        "warnings": explain.get("warnings") or [],
        "stats": explain.get("stats") or {},
    }
