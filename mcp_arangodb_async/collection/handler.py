"""Collection tool handler - dispatches collection operations."""

from typing import Any, Dict
from arango.database import StandardDatabase

from . import crud, batch, index, schema, management, backup
from ..utility.runtime_defaults import get_available_actions

OPERATIONS = {
    # CRUD (crud.py)
    "insert": crud.insert,
    "find": crud.find,
    "update": crud.update,
    "remove": crud.remove,
    "insert_with_validation": crud.insert_with_validation,
    "list": crud.list_collections,

    # Batch (batch.py)
    "bulk_insert": batch.bulk_insert,
    "bulk_update": batch.bulk_update,
    "import": batch.import_documents,
    "export": batch.export_documents,

    # Index (index.py)
    "list_indexes": index.list_indexes,
    "create_index": index.create_index,
    "delete_index": index.delete_index,

    # Schema (schema.py)
    "get_schema": schema.get_schema,
    "create_schema": schema.create_schema,
    "validate_document": schema.validate_document,
    "validate_references": schema.validate_references,

    # Management (management.py)
    "create": management.create_collection,
    "stats": management.stats,
    "drop": management.drop_collection,
    "truncate": management.truncate_collection,

    # Backup (backup.py)
    "backup": backup.backup,
}


def handle_collection(
    db: StandardDatabase, action: str, args: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Dispatch collection operations to appropriate handler.

    Args:
        db: ArangoDB database instance
        action: Operation name (e.g., 'insert', 'update', 'create_index')
        args: Operation arguments (optional for parameter-less operations like 'list')

    Returns:
        Operation result or error dictionary
    """
    if action not in OPERATIONS:
        available = get_available_actions("arango_collection")
        return {
            "error": f"Unknown action: {action}",
            "tool": "arango_collection",
            "available_actions": available,
            "hint": f"Use one of: {', '.join(available)}"
        }

    handler = OPERATIONS[action]

    try:
        if args is None:
            # For parameter-less operations
            return handler(db)
        else:
            return handler(db, args)
    except Exception as e:
        return {"error": str(e), "action": action}
