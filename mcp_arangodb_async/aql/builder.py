"""AQL query builder operations for ArangoDB."""

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
        if hasattr(cursor, "close"):
            try:
                cursor.close()
            except Exception:
                pass  # Ignore cleanup errors


def query_builder(
    db: StandardDatabase, args: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Build and execute a simple AQL query from structured filters/sort/limit.

    Operator model:
      Preconditions:
        - Database connection available.
        - Args include 'collection' (str).
        - Optional 'filters' with supported ops: ==, !=, <, <=, >, >=, IN, LIKE; values JSON-serializable.
        - Optional 'sort' [{field, direction}], 'limit' (int), 'return_fields' (projection fields).
      Effects:
        - Constructs AQL using bind variables for security and executes via AQL API.
        - Returns a list of documents or projected fields.
        - No mutations; performance depends on available indexes (may scan without indexes).
    """
    collection = args["collection"]
    filters = args.get("filters") or []
    sorts = args.get("sort") or []
    limit = args.get("limit")
    return_fields = args.get("return_fields")

    # Validate collection name to prevent injection
    # Hyphens excluded: unquoted AQL identifiers cannot contain hyphens
    if (
        not collection
        or not isinstance(collection, str)
        or not collection.replace("_", "").isalnum()
    ):
        raise ValueError("Invalid collection name")

    # Supported operators whitelist
    SUPPORTED_OPERATORS = {"==", "!=", "<", "<=", ">", ">=", "IN", "LIKE"}

    # Validate field names to prevent injection
    def _validate_field_name(field: str) -> str:
        if not field or not isinstance(field, str):
            raise ValueError("Invalid field name")
        # First char must be letter or underscore (AQL identifier rule)
        if not (field[0].isalpha() or field[0] == "_"):
            raise ValueError(f"Invalid field name: {field!r} (must start with letter or _)")
        # Allow alphanumeric, underscore, dot (for nested fields like user.email)
        if not all(c.isalnum() or c in "._" for c in field):
            raise ValueError(f"Invalid field name: {field!r}")
        return field

    filter_clauses: List[str] = []
    bind_vars: Dict[str, Any] = {}
    bind_counter = 0

    for f in filters:
        field = f.get("field")
        op = f.get("op")
        value = f.get("value")

        if not field or not op:
            continue

        # Validate operator
        if op not in SUPPORTED_OPERATORS:
            raise ValueError(f"Unsupported operator: {op}")

        # Validate and sanitize field name
        field = _validate_field_name(field)

        # Create bind variable
        bind_var = f"v{bind_counter}"
        bind_vars[bind_var] = value
        bind_counter += 1

        # Build clause with proper AQL syntax
        if op == "LIKE":
            # ArangoDB LIKE function: LIKE(doc.field, @value, case_insensitive)
            clause = f"LIKE(doc.{field}, @{bind_var}, true)"
        elif op == "IN":
            clause = f"doc.{field} IN @{bind_var}"
        else:
            clause = f"doc.{field} {op} @{bind_var}"
        filter_clauses.append(clause)

    filter_section = ""
    if filter_clauses:
        filter_section = "\n  FILTER " + " AND ".join(filter_clauses)

    sort_section = ""
    if sorts:
        sort_exprs = []
        for s in sorts:
            sort_field = s.get("field")
            direction = s.get("direction", "ASC")
            if sort_field:
                # Validate field name and direction
                sort_field = _validate_field_name(sort_field)
                if direction.upper() not in ("ASC", "DESC"):
                    direction = "ASC"
                sort_exprs.append(f"doc.{sort_field} {direction.upper()}")
        if sort_exprs:
            sort_section = "\n  SORT " + ", ".join(sort_exprs)

    limit_section = ""
    if limit:
        try:
            limit_val = int(limit)
            if limit_val > 0:
                bind_vars["limit_val"] = limit_val
                limit_section = "\n  LIMIT @limit_val"
        except (ValueError, TypeError):
            pass  # Ignore invalid limit

    # Build return clause
    if return_fields:
        # Validate return field names
        validated_fields = []
        for field in return_fields:
            if isinstance(field, str):
                try:
                    validated_field = _validate_field_name(field)
                    validated_fields.append(validated_field)
                except ValueError:
                    continue  # Skip invalid field names
        if validated_fields:
            ret = "{" + ", ".join([f"{f}: doc.{f}" for f in validated_fields]) + "}"
        else:
            ret = "doc"
    else:
        ret = "doc"

    aql = f"""
    FOR doc IN {collection}{filter_section}{sort_section}{limit_section}
      RETURN {ret}
    """

    cursor = db.aql.execute(aql, bind_vars=bind_vars)
    with safe_cursor(cursor):
        return list(cursor)
