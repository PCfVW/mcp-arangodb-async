"""Collection CRUD operations."""

from typing import Any, Dict, List, Optional
from arango.database import StandardDatabase

from ..utility.access_log import (
    log_access,
    log_query_results,
    ACCESS_TYPE_QUERY,
    ACCESS_TYPE_UPDATE,
)


def list_collections(
    db: StandardDatabase, args: Optional[Dict[str, Any]] = None
) -> List[str]:
    """Return non-system collection names (document + edge).

    Note: This operation uses Optional[Dict[str, Any]] = None signature pattern because:
    1. Semantic correctness - listing collections doesn't require any parameters
    2. Direct Python usage - allows calling list_collections(db) without args
    3. Backward compatibility - maintains the documented direct usage pattern

    Args:
        db: ArangoDB database instance
        args: Optional arguments (unused for this operation, maintained for MCP compatibility)

    Returns:
        List of non-system collection names

    Operator model:
      Preconditions:
        - Database connection available.
      Effects:
        - Reads and returns names of non-system collections.
        - No database mutations are performed.
    """
    cols = db.collections()
    names = [c["name"] for c in cols if not c.get("isSystem")]
    return names


def insert(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a document into a collection.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing 'collection' and 'document' keys.
              For backward compatibility, 'data' is accepted as an alias of 'document'.

    Returns:
        Dictionary with document metadata (_id, _key, _rev)

    Operator model:
      Preconditions:
        - Database connection available.
        - Target collection exists.
        - 'document' is a JSON-serializable object; may be subject to server-side constraints.
      Effects:
        - Inserts the document; returns inserted metadata.
        - Mutates the target collection.
    """
    collection_name = args.get("collection")
    if not isinstance(collection_name, str) or not collection_name:
        return {
            "error": "insert requires 'collection' parameter",
            "type": "MissingParameter",
        }
    document = args.get("document")
    if document is None:
        document = args.get("data")
    if document is None:
        return {
            "error": "insert requires 'document' (or legacy alias 'data') parameter",
            "type": "MissingParameter",
        }

    # Validate collection exists
    if not db.has_collection(collection_name):
        return {
            "error": f"Collection '{collection_name}' does not exist",
            "type": "CollectionNotFound",
        }

    col = db.collection(collection_name)
    result = col.insert(document)
    return {
        "_id": result.get("_id"),
        "_key": result.get("_key"),
        "_rev": result.get("_rev"),
    }


def update(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Update a document by key in a collection.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing 'collection', 'key', and 'update' keys

    Returns:
        Dictionary with updated document metadata (_id, _key, _rev)

    Operator model:
      Preconditions:
        - Database connection available.
        - Target collection exists and contains the document with given key.
      Effects:
        - Updates the document with provided fields; returns metadata.
        - Mutates the target collection.
    """
    collection_name = args.get("collection")
    if not isinstance(collection_name, str) or not collection_name:
        return {
            "error": "update requires 'collection' parameter",
            "type": "MissingParameter",
        }
    key = args.get("key")
    if not isinstance(key, str) or not key:
        return {
            "error": "update requires 'key' parameter",
            "type": "MissingParameter",
        }
    update_data = args.get("update")
    if update_data is None:
        update_data = args.get("data")
    if not isinstance(update_data, dict):
        return {
            "error": "update requires 'update' (or legacy alias 'data') object parameter",
            "type": "MissingParameter",
        }

    # Validate collection exists
    if not db.has_collection(collection_name):
        return {
            "error": f"Collection '{collection_name}' does not exist",
            "type": "CollectionNotFound",
        }

    col = db.collection(collection_name)
    payload = {"_key": key, **update_data}
    result = col.update(payload)
    return {
        "_id": result.get("_id"),
        "_key": result.get("_key"),
        "_rev": result.get("_rev"),
    }


def remove(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Remove a document by key from a collection.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing 'collection' and 'key' keys

    Returns:
        Dictionary with removed document metadata (_id, _key, _rev)

    Operator model:
      Preconditions:
        - Database connection available.
        - Target collection exists.
      Effects:
        - Removes the document by key; returns removal metadata.
        - Mutates the target collection.
    """
    collection_name = args.get("collection")
    if not isinstance(collection_name, str) or not collection_name:
        return {
            "error": "remove requires 'collection' parameter",
            "type": "MissingParameter",
        }
    key = args.get("key")
    if not isinstance(key, str) or not key:
        return {
            "error": "remove requires 'key' parameter",
            "type": "MissingParameter",
        }

    # Validate collection exists
    if not db.has_collection(collection_name):
        return {
            "error": f"Collection '{collection_name}' does not exist",
            "type": "CollectionNotFound",
        }

    col = db.collection(collection_name)
    result = col.delete(key)
    return {
        "_id": result.get("_id"),
        "_key": result.get("_key"),
        "_rev": result.get("_rev"),
    }


def find(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Find documents by key or filter criteria.

    Supports two modes:
    1. By key: Direct lookup via _key
    2. By filter: Query with MongoDB-style operators ($gt, $gte, $lt, $lte, $ne, $in)

    Args:
        db: ArangoDB database instance
        args: Dictionary containing 'collection', and either 'key' or 'filter'

    Returns:
        Dictionary with 'found'/'count' and 'doc'/'results'

    Operator model:
      Preconditions:
        - Database connection available; collection exists.
        - Either 'key' (for direct lookup) or 'filter' (for query) provided.
        - Filter operators must be one of: $gt, $gte, $lt, $lte, $ne, $in, or equality.
      Effects:
        - Executes query or direct lookup; no mutations.
        - Returns found document(s) or empty result.
    """
    collection_name = args["collection"]
    key = args.get("key")
    filter_ = args.get("filter")
    limit = args.get("limit", 100)

    # Validate collection exists
    if not db.has_collection(collection_name):
        return {
            "error": f"Collection '{collection_name}' does not exist",
            "type": "CollectionNotFound",
        }

    col = db.collection(collection_name)

    # Mode 1: By key (direct lookup)
    if key:
        doc = col.get(key)
        # Log access
        if doc and "_id" in doc:
            log_access(db, [doc["_id"]], ACCESS_TYPE_QUERY)
        return {
            "op": "find",
            "collection": collection_name,
            "found": doc is not None,
            "doc": doc,
        }

    # Mode 2: By filter (AQL query)
    if filter_:
        conditions = []
        bind_vars: Dict[str, Any] = {"@col": collection_name}

        for i, (field, value) in enumerate(filter_.items()):
            var = f"v{i}"
            bind_vars[var] = value

            if isinstance(value, dict):
                # Operator: {"$gt": 10}
                for op_name, op_val in value.items():
                    bind_vars[var] = op_val
                    if op_name == "$gt":
                        conditions.append(f"d.{field} > @{var}")
                    elif op_name == "$gte":
                        conditions.append(f"d.{field} >= @{var}")
                    elif op_name == "$lt":
                        conditions.append(f"d.{field} < @{var}")
                    elif op_name == "$lte":
                        conditions.append(f"d.{field} <= @{var}")
                    elif op_name == "$ne":
                        conditions.append(f"d.{field} != @{var}")
                    elif op_name == "$in":
                        conditions.append(f"d.{field} IN @{var}")
                    else:
                        conditions.append(f"d.{field} == @{var}")
            else:
                # Equality: field: value
                conditions.append(f"d.{field} == @{var}")

        where = " AND ".join(conditions) if conditions else "true"
        query = f"FOR d IN @@col FILTER {where} LIMIT {limit} RETURN d"

        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)

        # Log access
        log_query_results(db, results, ACCESS_TYPE_QUERY)

        return {
            "op": "find",
            "collection": collection_name,
            "count": len(results),
            "results": results,
        }

    return {
        "error": "find requires either 'key' or 'filter' parameter",
        "type": "MissingParameter",
    }


def insert_with_validation(
    db: StandardDatabase, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Insert a document after validating its reference fields.

    Operator model:
      Preconditions:
        - Database connection available; collection exists.
        - If 'reference_fields' provided, referenced documents should exist; otherwise insert aborts with report.
      Effects:
        - On valid refs, inserts the document and returns metadata.
        - Mutates the collection on successful insert.
    """
    ref_fields: List[str] = args.get("reference_fields") or []
    if ref_fields:
        # Reuse validation logic against a single document via AQL
        bind_vars = {"doc": args["document"], "fields": ref_fields}
        validation_query = """
        LET d = @doc
        LET invalid_refs = (
          FOR field IN @fields
            LET ref = DOCUMENT(d[field])
            FILTER ref == null AND d[field] != null
            RETURN {field: field, value: d[field]}
        )
        RETURN invalid_refs
        """
        invalid = list(db.aql.execute(validation_query, bind_vars=bind_vars))[0]
        if invalid:
            return {"error": "Invalid references", "invalid_references": invalid}
    col = db.collection(args["collection"])
    result = col.insert(args["document"])
    return {
        "_id": result.get("_id"),
        "_key": result.get("_key"),
        "_rev": result.get("_rev"),
    }
