"""Collection schema operations."""

from typing import Any, Dict
from jsonschema import Draft7Validator, ValidationError as JSONSchemaValidationError
from arango.database import StandardDatabase


def _validate_collection_name(name: str) -> str:
    """Validate collection name to prevent AQL injection.

    Only allows alphanumerics and underscores. Hyphens excluded: unquoted AQL
    identifiers cannot contain hyphens (parsed as subtraction).
    """
    if not name or not isinstance(name, str):
        raise ValueError("Invalid collection name")
    if not name.replace("_", "").isalnum():
        raise ValueError(f"Invalid collection name: {name!r} (only [A-Za-z0-9_] allowed)")
    return name


def _validate_field_name(field: str) -> str:
    """Validate field name to prevent AQL injection.

    AQL attribute identifiers must start with a letter or underscore and
    contain only alphanumerics, underscores, or dots (for nested paths).
    """
    if not field or not isinstance(field, str):
        raise ValueError("Invalid field name")
    if not (field[0].isalpha() or field[0] == "_"):
        raise ValueError(f"Invalid field name: {field!r} (must start with letter or _)")
    if not all(c.isalnum() or c in "._" for c in field):
        raise ValueError(f"Invalid field name: {field!r}")
    return field


def get_schema(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Get stored JSON Schema for a collection.

    Retrieves schema stored with key '<collection>:<schema_name>'.

    Operator model:
      Preconditions:
        - Database connection available.
        - 'mcp_schemas' collection exists (schema storage).
        - Schema was previously created with matching collection and name.
      Effects:
        - Queries 'mcp_schemas' collection for stored schema.
        - Returns the schema definition if found; error if not found or collection missing.
        - No database mutations are performed.
    """
    collection = args["collection"]
    schema_name = args.get("schema_name", "default")

    if not db.has_collection("mcp_schemas"):
        return {
            "error": "No schemas found - 'mcp_schemas' collection does not exist",
            "collection": collection,
            "schema_name": schema_name,
        }

    col = db.collection("mcp_schemas")
    key = f"{collection}:{schema_name}"
    stored = col.get(key)

    if not stored:
        return {
            "error": f"Schema not found: {key}",
            "collection": collection,
            "schema_name": schema_name,
        }

    return {
        "found": True,
        "collection": collection,
        "schema_name": schema_name,
        "schema": stored.get("schema"),
    }


def create_schema(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a named JSON Schema for a collection.

    Stored in a dedicated collection 'mcp_schemas' with key '<collection>:<name>'.

    Operator model:
      Preconditions:
        - Database connection available.
        - Args include 'name' (str), 'collection' (str), and a JSON object under 'schema'/'schema_def'.
        - Provided schema is Draft-07 compatible (validated via Draft7Validator.check_schema).
      Effects:
        - Ensures collection 'mcp_schemas' exists (creates if missing).
        - Upserts document with _key '<collection>:<name>' containing the schema payload.
        - Returns {"created": True, "key": key} on success.
        - Does not validate any user documents; only stores/compiles schema.
    """
    name = args["name"]
    collection = args["collection"]
    schema = args.get("schema_def", args.get("schema"))
    if schema is None:
        raise ValueError(
            "Missing schema definition (expected 'schema' or 'schema_def')"
        )
    key = f"{collection}:{name}"
    # Ensure schema collection exists
    if not db.has_collection("mcp_schemas"):
        db.create_collection("mcp_schemas", edge=False)
    col = db.collection("mcp_schemas")
    doc = {"_key": key, "collection": collection, "name": name, "schema": schema}
    try:
        # upsert semantics
        if col.has(key) if hasattr(col, "has") else False:  # type: ignore[attr-defined]
            col.replace(doc)
        else:
            col.insert(doc)
    except Exception:
        # Fallback: try replace then insert
        try:
            col.replace(doc)
        except Exception:
            col.insert(doc)
    # basic validation compilation
    Draft7Validator.check_schema(schema)
    return {"created": True, "key": key}


def validate_document(
    db: StandardDatabase, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate a document against a stored or inline JSON Schema.

    Operator model:
      Preconditions:
        - Database connection available.
        - Args include 'collection' (str) and 'document' (object).
        - Either an inline 'schema'/'schema_def' is provided, or 'schema_name' refers to an existing stored schema with key '<collection>:<schema_name>'.
      Effects:
        - If 'schema_name' is provided, reads schema from 'mcp_schemas'.
        - Validates the document against the Draft-07 schema.
        - Returns {"valid": True} when no violations; otherwise {"valid": False, "errors": [...] }.
        - No database mutations are performed.
    """
    collection = args["collection"]
    document = args["document"]
    schema = args.get("schema_def", args.get("schema"))
    schema_name = args.get("schema_name")
    if schema is None:
        if not schema_name:
            raise ValueError("Either 'schema' or 'schema_name' must be provided")
        key = f"{collection}:{schema_name}"
        if not db.has_collection("mcp_schemas"):
            raise ValueError(
                "No stored schemas found (collection 'mcp_schemas' missing)"
            )
        col = db.collection("mcp_schemas")
        stored = col.get(key)
        if not stored:
            raise ValueError(f"Stored schema not found: {key}")
        schema = stored.get("schema")
    try:
        validator = Draft7Validator(schema)
        errors = sorted(validator.iter_errors(document), key=lambda e: e.path)
        if errors:
            return {
                "valid": False,
                "errors": [
                    {
                        "message": e.message,
                        "path": list(e.path),
                        "validator": e.validator,
                    }
                    for e in errors
                ],
            }
        return {"valid": True}
    except JSONSchemaValidationError as e:
        return {"valid": False, "errors": [{"message": str(e)}]}


def validate_references(
    db: StandardDatabase, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Validate that reference fields contain valid document IDs.

    Operator model:
      Preconditions:
        - Database connection available; collection exists.
        - 'reference_fields' provided; documents use ArangoDB id format where applicable.
      Effects:
        - Analyzes documents and returns invalid reference report; optionally deletes invalid documents if 'fix_invalid' is true.
        - Mutates the collection only when 'fix_invalid' is true.
    """
    from contextlib import contextmanager

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

    collection_name = _validate_collection_name(args["collection"])
    collection = db.collection(collection_name)
    raw_ref_fields: list[str] = args.get("reference_fields") or []
    # AQL `doc[field]` only resolves top-level attributes; dots are forbidden here
    # (doc["user.email"] looks for a literal key "user.email", not nested access)
    ref_fields = []
    for f in raw_ref_fields:
        validated = _validate_field_name(f)
        if "." in validated:
            raise ValueError(
                f"Reference field {f!r} contains a dot. "
                "Only top-level fields are supported (doc[field] does not traverse nested paths)."
            )
        ref_fields.append(validated)

    # Use bind vars for ref_fields to prevent AQL injection
    validation_query = f"""
    FOR doc IN {collection_name}
      LET invalid_refs = (
        FOR field IN @ref_fields
          LET ref = DOCUMENT(doc[field])
          FILTER ref == null AND doc[field] != null
          RETURN {{field: field, value: doc[field]}}
      )
      FILTER LENGTH(invalid_refs) > 0
      RETURN {{ _id: doc._id, _key: doc._key, invalid_references: invalid_refs }}
    """
    cursor = db.aql.execute(validation_query, bind_vars={"ref_fields": ref_fields})
    with safe_cursor(cursor):
        invalid_docs = list(cursor)
    result: Dict[str, Any] = {
        "total_checked": collection.count() if hasattr(collection, "count") else None,
        "invalid_count": len(invalid_docs),
        "invalid_documents": invalid_docs[:100],
        "validation_passed": len(invalid_docs) == 0,
    }
    if args.get("fix_invalid") and invalid_docs:
        keys_to_remove = [doc["_key"] for doc in invalid_docs]
        try:
            collection.delete_many(keys_to_remove)
            result["removed_count"] = len(keys_to_remove)
        except Exception:
            result["removed_count"] = 0
    return result
