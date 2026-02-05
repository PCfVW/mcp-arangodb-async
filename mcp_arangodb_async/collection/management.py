"""Collection management operations."""

from typing import Any, Dict, Optional
from arango.database import StandardDatabase


def create_collection(
    db: StandardDatabase, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a collection (document or edge) or get existing one.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing 'name', optional 'type' and 'waitForSync'

    Returns:
        Dictionary with collection properties (name, type, waitForSync)

    Operator model:
      Preconditions:
        - Database connection available.
        - 'name' is a valid collection name; 'type' in {document, edge}.
      Effects:
        - Creates the collection if missing (edge/document as specified) or returns existing properties.
        - Mutates database when creating; otherwise read-only.
    """
    name = args["name"]
    typ = args.get("type", "document")
    edge = True if typ == "edge" else False
    wait_for_sync: Optional[bool] = args.get("waitForSync")

    # Create if missing, otherwise get handle
    if not db.has_collection(name):
        col = (
            db.create_collection(name, edge=edge, sync=wait_for_sync)
            if wait_for_sync is not None
            else db.create_collection(name, edge=edge)
        )
    else:
        col = db.collection(name)

    # Fetch properties to map type precisely
    props = col.properties()  # dict
    arango_type = props.get("type")  # 2=document, 3=edge
    mapped_type = "edge" if arango_type == 3 else "document"
    return {
        "name": props.get("name", name),
        "type": mapped_type,
        "waitForSync": props.get("waitForSync"),
    }


def stats(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Get statistics for a collection.

    Returns document count, revision count, figures, and other metadata.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing 'collection' (collection name)

    Returns:
        Dictionary with statistics (count, figures, etc.)

    Operator model:
      Preconditions:
        - Database connection available; collection exists.
      Effects:
        - Queries collection metadata; no mutations.
        - Returns statistical information about the collection.
    """
    collection_name = args["collection"]

    # Validate collection exists
    if not db.has_collection(collection_name):
        return {
            "error": f"Collection '{collection_name}' does not exist",
            "type": "CollectionNotFound",
        }

    col = db.collection(collection_name)

    try:
        # Get collection properties
        props = col.properties()
        count = col.count()

        # Build statistics
        stats_result = {
            "collection": collection_name,
            "count": count,
            "type": props.get("type"),  # 2=document, 3=edge
            "isSystem": props.get("isSystem", False),
            "waitForSync": props.get("waitForSync", False),
            "keyOptions": props.get("keyOptions"),
            "cacheEnabled": props.get("cacheEnabled"),
        }

        # Add figures if available (size, memory, etc.)
        if hasattr(col, "figures"):
            try:
                figures = col.figures()
                stats_result["figures"] = figures
            except Exception:
                pass  # Ignore if figures not available

        return stats_result

    except Exception as e:
        return {
            "error": str(e),
            "type": "StatisticsError",
            "collection": collection_name,
        }


def drop_collection(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Drop (delete) a collection.

    Removes the collection and all its documents from the database.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing 'collection' (collection name)

    Returns:
        Dictionary with success status

    Operator model:
      Preconditions:
        - Database connection available.
        - Collection exists (or safe to ignore if not).
      Effects:
        - Deletes the collection and all its data from the database.
        - Mutates database irreversibly.
    """
    collection_name = args["collection"]

    if not db.has_collection(collection_name):
        return {
            "error": f"Collection '{collection_name}' does not exist",
            "type": "CollectionNotFound",
            "collection": collection_name,
        }

    try:
        db.delete_collection(collection_name)
        return {
            "success": True,
            "collection": collection_name,
            "action": "dropped",
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": "DropError",
            "collection": collection_name,
        }


def truncate_collection(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Truncate (empty) a collection.

    Removes all documents from a collection but keeps the collection structure.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing 'collection' (collection name)

    Returns:
        Dictionary with success status and affected count

    Operator model:
      Preconditions:
        - Database connection available; collection exists.
      Effects:
        - Removes all documents from the collection.
        - Keeps indexes, schema, and collection properties intact.
        - Mutates collection irreversibly.
    """
    collection_name = args["collection"]

    if not db.has_collection(collection_name):
        return {
            "error": f"Collection '{collection_name}' does not exist",
            "type": "CollectionNotFound",
            "collection": collection_name,
        }

    try:
        col = db.collection(collection_name)
        count_before = col.count()
        col.truncate()
        count_after = col.count()

        return {
            "success": True,
            "collection": collection_name,
            "action": "truncated",
            "documents_removed": count_before - count_after,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": "TruncateError",
            "collection": collection_name,
        }
