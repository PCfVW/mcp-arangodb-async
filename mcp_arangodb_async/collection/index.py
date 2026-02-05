"""Collection index operations."""

from typing import Any, Dict, List
from arango.database import StandardDatabase


def list_indexes(
    db: StandardDatabase, args: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """List indexes for a given collection (simplified fields).

    Operator model:
      Preconditions:
        - Database connection available; target collection exists.
      Effects:
        - Reads and returns index metadata for the collection.
        - No database mutations.
    """
    col = db.collection(args["collection"])
    indexes = col.indexes()  # list of dicts
    simplified: List[Dict[str, Any]] = []
    for ix in indexes:
        simplified.append(
            {
                "id": ix.get("id"),
                "type": ix.get("type"),
                "fields": ix.get("fields"),
                "unique": ix.get("unique"),
                "sparse": ix.get("sparse"),
                "name": ix.get("name"),
                "selectivityEstimate": ix.get("selectivityEstimate"),
            }
        )
    return simplified


def create_index(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Create an index for a collection, supporting all common index types.

    Supported types: persistent, hash, skiplist, ttl, fulltext, geo

    Operator model:
      Preconditions:
        - Database connection available; target collection exists.
        - 'fields' non-empty; type-specific options valid (e.g., ttl requires 'ttl' seconds).
      Effects:
        - Creates the specified index and returns its metadata.
        - Mutates the collection's index set.
    """
    col = db.collection(args["collection"])
    ix_type = args.get("type", "persistent")
    fields = args["fields"]

    # Build index data dictionary for unified add_index() API (python-arango 8.x)
    index_data = {
        "type": ix_type,
        "fields": fields,
    }

    # Add common optional parameters
    if args.get("unique") is not None:
        index_data["unique"] = bool(args["unique"])
    if args.get("sparse") is not None:
        index_data["sparse"] = bool(args["sparse"])
    if args.get("deduplicate") is not None:
        index_data["deduplicate"] = bool(args["deduplicate"])
    if args.get("name") is not None:
        index_data["name"] = args["name"]
    if args.get("inBackground") is not None:
        index_data["inBackground"] = args["inBackground"]

    # Add type-specific parameters
    if ix_type == "ttl":
        # TTL index requires a single field and expireAfter seconds
        if not fields or len(fields) != 1:
            raise ValueError("TTL index requires exactly one field in 'fields'")
        expire_after = args.get("ttl") or args.get("expireAfter")
        if expire_after is None:
            raise ValueError("TTL index requires 'ttl' (expireAfter seconds)")
        index_data["expireAfter"] = expire_after
    elif ix_type == "fulltext":
        # Fulltext index supports minLength optionally
        if args.get("minLength") is not None:
            index_data["minLength"] = args["minLength"]
    elif ix_type == "geo":
        # Geo index can be on one or two fields; geoJson optional
        if args.get("geoJson") is not None:
            index_data["geoJson"] = args["geoJson"]

    # Use unified add_index() method (python-arango 8.x recommended API)
    # formatter=True for backward compatibility with snake_case field names
    created = col.add_index(index_data, formatter=True)

    # Return formatted index info
    return {
        "id": created.get("id"),
        "type": created.get("type"),
        "fields": created.get("fields"),
        "unique": created.get("unique"),
        "sparse": created.get("sparse"),
        "name": created.get("name"),
    }


def delete_index(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Delete an index, accepting index id (collection/12345) or index name.

    Operator model:
      Preconditions:
        - Database connection available; target collection exists.
        - Index id exists or name resolves to an existing index.
      Effects:
        - Deletes the index; returns confirmation and id used.
        - Mutates the collection's index set.
    """
    collection = args["collection"]
    id_or_name = args["id_or_name"]

    # Resolve index id if a name was provided
    index_id = id_or_name
    if "/" not in id_or_name:
        # assume it's a name; look up by name
        col = db.collection(collection)
        for ix in col.indexes():
            if ix.get("name") == id_or_name:
                index_id = ix.get("id")
                break
        else:
            raise ValueError(
                f"Index with name '{id_or_name}' not found in collection '{collection}'"
            )

    # If the id did not include a slash, prepend collection name
    if "/" not in index_id:
        index_id = f"{collection}/{index_id}"

    result = db.delete_index(index_id)
    return {"deleted": True, "id": index_id, "result": result}
