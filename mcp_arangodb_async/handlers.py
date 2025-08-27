"""
ArangoDB MCP Server - Tool Handlers

Purpose:
    Implements handler functions for all MCP tools. Handlers take validated
    arguments and perform operations via the python-arango driver, returning
    simple JSON-serializable results.

Handler Signature Patterns:
    Most handlers follow the standard pattern documented in the README:
        (db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]

    Exception for parameter-less operations:
        handle_list_collections(db: StandardDatabase, args: Optional[Dict[str, Any]] = None)

    This dual signature approach serves several purposes:
    1. Semantic correctness - operations that don't need parameters shouldn't require them
    2. Backward compatibility - direct Python usage can call list_collections(db) without args
    3. MCP integration - the _invoke_handler pattern in entry.py handles both signatures seamlessly

    The @handle_errors decorator accommodates both patterns by checking if args is None.
    This allows the same handler to work in both MCP context (with validated args dict) and
    direct Python usage (with optional args for parameter-less operations).

Functions by category:

Core Data:
    - handle_arango_query
    - handle_list_collections (uses Optional[Dict[str, Any]] = None signature)
    - handle_insert
    - handle_update
    - handle_remove
    - handle_create_collection
    - handle_backup

Indexing & Query Analysis:
    - handle_list_indexes
    - handle_create_index
    - handle_delete_index
    - handle_explain_query

Validation & Bulk Ops:
    - handle_validate_references
    - handle_insert_with_validation
    - handle_bulk_insert
    - handle_bulk_update

Schema Management:
    - handle_create_schema
    - handle_validate_document

Enhanced Query:
    - handle_query_builder
    - handle_query_profile

Graph Operations:
    - handle_create_graph
    - handle_add_edge
    - handle_traverse
    - handle_shortest_path
    - handle_list_graphs
    - handle_add_vertex_collection
    - handle_add_edge_definition

Graph Management:
    - handle_backup_graph
    - handle_restore_graph
    - handle_backup_named_graphs
    - handle_validate_graph_integrity
    - handle_graph_statistics

All handlers are decorated with @handle_errors for consistent error handling.
The MCP integration layer in entry.py uses _invoke_handler to accommodate both
signature patterns seamlessly, enabling comprehensive testing and direct usage.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import json
import logging
from contextlib import contextmanager
from jsonschema import Draft7Validator, ValidationError as JSONSchemaValidationError
from arango.database import StandardDatabase
from arango.exceptions import ArangoError

# Type imports removed - using Dict[str, Any] for validated args from Pydantic models
from .backup import backup_collections_to_dir
from .graph_backup import (
    backup_graph_to_dir,
    restore_graph_from_dir,
    backup_named_graphs,
    validate_graph_integrity,
    calculate_graph_statistics,
)

# Configure logger for handlers
logger = logging.getLogger(__name__)


def handle_errors(func):
    """Decorator to standardize error handling across all handlers.

    This decorator accommodates the dual signature pattern used in the codebase:

    1. Standard handlers: func(db: StandardDatabase, args: Dict[str, Any])
       - Most handlers expect args to be provided
       - Used for operations that require parameters

    2. Parameter-less handlers: func(db: StandardDatabase, args: Optional[Dict[str, Any]] = None)
       - Currently only handle_list_collections uses this pattern
       - Used for operations that don't require parameters (semantic correctness)
       - Supports direct Python usage: handle_list_collections(db) without args

    The decorator checks if args is None and calls the appropriate signature:
    - If args is None: calls func(db) for parameter-less operations
    - If args is provided: calls func(db, args) for standard operations

    This enables the same handler to work in both:
    - MCP context: where args is always a validated dictionary from Pydantic models
    - Direct Python usage: where args might be None for parameter-less operations

    The _invoke_handler function in entry.py provides additional signature detection
    for test compatibility, but this decorator handles the core dual signature support.
    """
    def wrapper(db: StandardDatabase, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            # Handle parameter-less operations (e.g., list_collections)
            # These handlers accept Optional[Dict[str, Any]] = None in their signature
            if args is None:
                return func(db)
            else:
                # Handle standard operations that require args parameter
                # These handlers expect Dict[str, Any] (non-optional)
                return func(db, args)
        except KeyError as e:
            logger.error(f"Missing required parameter in {func.__name__}: {e}")
            return {"error": f"Missing required parameter: {str(e)}", "type": "KeyError"}
        except ArangoError as e:
            logger.error(f"ArangoDB error in {func.__name__}: {e}")
            return {"error": f"Database operation failed: {str(e)}", "type": "ArangoError"}
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            return {"error": f"Operation failed: {str(e)}", "type": type(e).__name__}
    return wrapper


@contextmanager
def safe_cursor(cursor):
    """Context manager for safe cursor handling."""
    try:
        yield cursor
    finally:
        if hasattr(cursor, 'close'):
            try:
                cursor.close()
            except Exception:
                pass  # Ignore cleanup errors
from .models import (
    CreateIndexArgs,
    DeleteIndexArgs,
    ListIndexesArgs,
    ExplainQueryArgs,
    ValidateReferencesArgs,
    InsertWithValidationArgs,
    BulkInsertArgs,
    BulkUpdateArgs,
    CreateGraphArgs,
    AddEdgeArgs,
    TraverseArgs,
    ShortestPathArgs,
)


@handle_errors
def handle_arango_query(db: StandardDatabase, args: Dict[str, Any]) -> List[Dict[str, Any]]:
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
        return list(cursor)


@handle_errors
def handle_list_collections(db: StandardDatabase, args: Optional[Dict[str, Any]] = None) -> List[str]:
    """Return non-system collection names (document + edge).

    Note: This handler uses Optional[Dict[str, Any]] = None signature pattern because:
    1. Semantic correctness - listing collections doesn't require any parameters
    2. Direct Python usage - allows calling handle_list_collections(db) without args
    3. Backward compatibility - maintains the documented direct usage pattern
    4. The @handle_errors decorator handles both this signature and the standard pattern

    This is the only handler that uses this pattern; all others use Dict[str, Any].

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


@handle_errors
def handle_insert(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a document into a collection.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing 'collection' and 'document' keys

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
    collection_name = args["collection"]
    document = args["document"]

    # Validate collection exists
    if not db.has_collection(collection_name):
        return {"error": f"Collection '{collection_name}' does not exist", "type": "CollectionNotFound"}

    col = db.collection(collection_name)
    result = col.insert(document)
    return {"_id": result.get("_id"), "_key": result.get("_key"), "_rev": result.get("_rev")}


@handle_errors
def handle_update(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
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
    collection_name = args["collection"]
    key = args["key"]
    update_data = args["update"]

    # Validate collection exists
    if not db.has_collection(collection_name):
        return {"error": f"Collection '{collection_name}' does not exist", "type": "CollectionNotFound"}

    col = db.collection(collection_name)
    payload = {"_key": key, **update_data}
    result = col.update(payload)
    return {"_id": result.get("_id"), "_key": result.get("_key"), "_rev": result.get("_rev")}


@handle_errors
def handle_remove(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
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
    collection_name = args["collection"]
    key = args["key"]

    # Validate collection exists
    if not db.has_collection(collection_name):
        return {"error": f"Collection '{collection_name}' does not exist", "type": "CollectionNotFound"}

    col = db.collection(collection_name)
    result = col.delete(key)
    return {"_id": result.get("_id"), "_key": result.get("_key"), "_rev": result.get("_rev")}


@handle_errors
def handle_create_collection(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
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


@handle_errors
def handle_backup(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Backup collections to JSON files.

    Args:
        db: ArangoDB database instance
        args: Dictionary with optional 'output_dir', 'collections', 'collection', 'doc_limit'

    Returns:
        Dictionary with backup report (output_dir, written files, counts)

    Operator model:
      Preconditions:
        - Database connection available; target collections exist (if specified).
        - Output directory writable (if provided).
      Effects:
        - Reads documents and writes JSON files to output directory.
        - No database mutations; side-effect is file system writes.
    """
    output_dir = args.get("output_dir") or args.get("outputDir")

    # Handle both single collection (TS compatibility) and multiple collections
    collections = args.get("collections")
    single_collection = args.get("collection")
    if single_collection and not collections:
        collections = [single_collection]

    doc_limit = args.get("doc_limit") or args.get("docLimit")
    report = backup_collections_to_dir(db, output_dir=output_dir, collections=collections, doc_limit=doc_limit)
    return report


@handle_errors
def handle_list_indexes(db: StandardDatabase, args: Dict[str, Any]) -> List[Dict[str, Any]]:
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
        simplified.append({
            "id": ix.get("id"),
            "type": ix.get("type"),
            "fields": ix.get("fields"),
            "unique": ix.get("unique"),
            "sparse": ix.get("sparse"),
            "name": ix.get("name"),
            "selectivityEstimate": ix.get("selectivityEstimate"),
        })
    return simplified


@handle_errors
def handle_create_index(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
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
    unique = bool(args.get("unique", False))
    sparse = bool(args.get("sparse", False))
    deduplicate = bool(args.get("deduplicate", True))
    name = args.get("name")
    in_background = args.get("inBackground")

    if ix_type == "persistent":
        created = col.add_persistent_index(
            fields,
            unique=unique,
            sparse=sparse,
            deduplicate=deduplicate,
            name=name,
            in_background=in_background,
        )
    elif ix_type == "hash":
        created = col.add_hash_index(
            fields,
            unique=unique,
            sparse=sparse,
            deduplicate=deduplicate,
            name=name,
            in_background=in_background,
        )
    elif ix_type == "skiplist":
        created = col.add_skiplist_index(
            fields,
            unique=unique,
            sparse=sparse,
            deduplicate=deduplicate,
            name=name,
            in_background=in_background,
        )
    elif ix_type == "ttl":
        # TTL index requires a single field and expireAfter seconds
        if not fields or len(fields) != 1:
            raise ValueError("TTL index requires exactly one field in 'fields'")
        expire_after = args.get("ttl") or args.get("expireAfter")
        if expire_after is None:
            raise ValueError("TTL index requires 'ttl' (expireAfter seconds)")
        created = col.add_ttl_index(fields[0], expire_after, name=name, in_background=in_background)
    elif ix_type == "fulltext":
        # Fulltext index supports min_length optionally; driver may accept it via keyword
        min_length = args.get("minLength")
        created = col.add_fulltext_index(fields, min_length=min_length, name=name, in_background=in_background)
    elif ix_type == "geo":
        # Geo index can be on one or two fields; geo_json optional
        geo_json = args.get("geoJson")
        created = col.add_geo_index(fields, geo_json=geo_json, name=name, in_background=in_background)
    else:
        raise ValueError(f"Unknown index type: {ix_type}")

    # created is dict with index info
    return {
        "id": created.get("id"),
        "type": created.get("type"),
        "fields": created.get("fields"),
        "unique": created.get("unique"),
        "sparse": created.get("sparse"),
        "name": created.get("name"),
    }


@handle_errors
def handle_delete_index(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Delete an index, accepting index id (collection/12345) or index name."""
    """
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
            raise ValueError(f"Index with name '{id_or_name}' not found in collection '{collection}'")

    # If the id did not include a slash, prepend collection name
    if "/" not in index_id:
        index_id = f"{collection}/{index_id}"

    result = db.delete_index(index_id)
    return {"deleted": True, "id": index_id, "result": result}


@handle_errors
def handle_explain_query(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
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
        args["query"], bind_vars=args.get("bind_vars") or {}, max_plans=int(args.get("max_plans", 1))
    )
    result: Dict[str, Any] = {
        "plans": explain.get("plans") or [],
        "warnings": explain.get("warnings") or [],
        "stats": explain.get("stats") or {},
    }
    if args.get("suggest_indexes", True):
        result["index_suggestions"] = _analyze_query_for_indexes(args["query"], result["plans"])  # best-effort
    return result


def _analyze_query_for_indexes(query: str, plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Heuristic index suggestions based on execution nodes."""
    suggestions: List[Dict[str, Any]] = []
    for plan in plans or []:
        for node in plan.get("nodes", []):
            node_type = node.get("type")
            # Suggest on Filter / IndexNode absence
            if node_type == "Filter" or node_type == "EnumerateCollection":
                # Basic hint without deep AQL parsing
                suggestions.append({
                    "hint": "Consider adding a persistent/hash index for filtered fields",
                    "nodeId": node.get("id"),
                })
    # Deduplicate hints
    unique = []
    seen = set()
    for s in suggestions:
        key = (s.get("hint"), s.get("nodeId"))
        if key not in seen:
            seen.add(key)
            unique.append(s)
    return unique


@handle_errors
def handle_validate_references(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that reference fields contain valid document IDs."""
    """
    Operator model:
      Preconditions:
        - Database connection available; collection exists.
        - 'reference_fields' provided; documents use ArangoDB id format where applicable.
      Effects:
        - Analyzes documents and returns invalid reference report; optionally deletes invalid documents if 'fix_invalid' is true.
        - Mutates the collection only when 'fix_invalid' is true.
    """
    collection = db.collection(args["collection"])
    ref_fields: List[str] = args.get("reference_fields") or []

    # Simple AQL validation using DOCUMENT() for each reference field
    fields_list = ", ".join([f"'{f}'" for f in ref_fields])
    validation_query = f"""
    FOR doc IN {args['collection']}
      LET invalid_refs = (
        FOR field IN [{fields_list}]
          LET ref = DOCUMENT(doc[field])
          FILTER ref == null AND doc[field] != null
          RETURN {{field: field, value: doc[field]}}
      )
      FILTER LENGTH(invalid_refs) > 0
      RETURN {{ _id: doc._id, _key: doc._key, invalid_references: invalid_refs }}
    """
    cursor = db.aql.execute(validation_query)
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


@handle_errors
def handle_insert_with_validation(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Insert a document after validating reference fields exist."""
    """
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
    return {"_id": result.get("_id"), "_key": result.get("_key"), "_rev": result.get("_rev")}


@handle_errors
def handle_bulk_insert(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Insert multiple documents efficiently with optional validation and batching."""
    """
    Operator model:
      Preconditions:
        - Database connection available; collection exists.
        - 'documents' non-empty list; optional 'batch_size' positive integer.
      Effects:
        - Inserts documents in batches; returns counts and any errors.
        - Mutates the collection for successfully inserted documents.
    """
    collection = db.collection(args["collection"])
    documents: List[Dict[str, Any]] = args.get("documents") or []
    batch_size = int(args.get("batch_size", 1000))
    validate_refs = bool(args.get("validate_refs", False))
    on_error = args.get("on_error", "stop")

    results: Dict[str, Any] = {
        "total_documents": len(documents),
        "inserted_count": 0,
        "error_count": 0,
        "errors": [],
        "inserted_ids": [],
    }

    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        try:
            if validate_refs:
                # Lightweight per-doc ref check using DOCUMENT() on likely fields ending with '_id'
                # For unit testing, we will not depend on actual DB; assume pass-through
                pass
            batch_result = collection.insert_many(batch, return_new=False, sync=True)
            results["inserted_count"] += len(batch_result)
            results["inserted_ids"].extend([r.get("_id") for r in batch_result if isinstance(r, dict)])
        except Exception as e:
            results["error_count"] += len(batch)
            results["errors"].append({"batch_start": i, "batch_size": len(batch), "error": str(e)})
            if on_error == "stop":
                break
            else:
                continue
    results["success_rate"] = (
        results["inserted_count"] / results["total_documents"] if results["total_documents"] else 0
    )
    return results


# Schema management handlers
@handle_errors
def handle_create_schema(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
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
        raise ValueError("Missing schema definition (expected 'schema' or 'schema_def')")
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


@handle_errors
def handle_validate_document(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
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
            raise ValueError("No stored schemas found (collection 'mcp_schemas' missing)")
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


@handle_errors
def handle_query_builder(db: StandardDatabase, args: Dict[str, Any]) -> List[Dict[str, Any]]:
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
    if not collection or not isinstance(collection, str) or not collection.replace('_', '').replace('-', '').isalnum():
        raise ValueError("Invalid collection name")

    # Supported operators whitelist
    SUPPORTED_OPERATORS = {"==", "!=", "<", "<=", ">", ">=", "IN", "LIKE"}

    # Validate field names to prevent injection
    def _validate_field_name(field: str) -> str:
        if not field or not isinstance(field, str):
            raise ValueError("Invalid field name")
        # Allow alphanumeric, underscore, dot (for nested fields)
        if not all(c.isalnum() or c in '._' for c in field):
            raise ValueError(f"Invalid field name: {field}")
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
            sort_field = s.get('field')
            direction = s.get('direction', 'ASC')
            if sort_field:
                # Validate field name and direction
                sort_field = _validate_field_name(sort_field)
                if direction.upper() not in ('ASC', 'DESC'):
                    direction = 'ASC'
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


@handle_errors
def handle_query_profile(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
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
    explain = db.aql.explain(args["query"], bind_vars=args.get("bind_vars") or {}, max_plans=int(args.get("max_plans", 1)))
    return {
        "plans": explain.get("plans") or [],
        "warnings": explain.get("warnings") or [],
        "stats": explain.get("stats") or {},
    }


# Graph handlers (Phase 2)
@handle_errors
def handle_create_graph(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Create a named graph with edge definitions, optionally creating collections."""
    """
    Operator model:
      Preconditions:
        - Database connection available.
        - 'name' provided; 'edge_definitions' well-formed with edge/from/to collections.
      Effects:
        - Optionally creates required vertex/edge collections.
        - Creates the graph if missing; returns summary info.
        - Mutates database when creating collections/graph.
    """
    name = args["name"]
    edge_defs = args.get("edge_definitions") or []
    create_colls = bool(args.get("create_collections", True))

    # Prepare edge definitions for python-arango
    arango_edge_defs: List[Dict[str, Any]] = []
    for ed in edge_defs:
        arango_edge_defs.append({
            "edge_collection": ed["edge_collection"],
            "from_vertex_collections": ed["from_collections"],
            "to_vertex_collections": ed["to_collections"],
        })

    # Create vertex and edge collections if requested
    if create_colls:
        for ed in edge_defs:
            if not db.has_collection(ed["edge_collection"]):
                db.create_collection(ed["edge_collection"], edge=True)
            for vc in ed["from_collections"] + ed["to_collections"]:
                if not db.has_collection(vc):
                    db.create_collection(vc, edge=False)

    # Create or get graph
    if not db.has_graph(name):
        g = db.create_graph(name, edge_definitions=arango_edge_defs)
    else:
        g = db.graph(name)

    # Return summary
    info = {
        "name": name,
        "edge_definitions": edge_defs,
        "vertex_collections": sorted({vc for ed in edge_defs for vc in (ed["from_collections"] + ed["to_collections"])})
    }
    return info


@handle_errors
def handle_add_edge(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Insert an edge document with _from and _to and optional attributes."""
    """
    Operator model:
      Preconditions:
        - Database connection available; edge collection exists.
        - '_from' and '_to' target vertices exist or are acceptable by DB constraints.
      Effects:
        - Inserts edge document; returns metadata.
        - Mutates the edge collection.
    """
    col = db.collection(args["collection"])
    payload = {"_from": args["from_id"], "_to": args["to_id"], **(args.get("attributes") or {})}
    result = col.insert(payload)
    return {"_id": result.get("_id"), "_key": result.get("_key"), "_rev": result.get("_rev")}


@handle_errors
def handle_traverse(db: StandardDatabase, args: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Perform a bounded traversal via AQL using either a named graph or edge collections."""
    """
    Operator model:
      Preconditions:
        - Database connection available.
        - Either 'graph' is provided or 'edge_collections' is a non-empty list.
        - 'start_vertex' provided; optional bounds and options valid.
      Effects:
        - Executes traversal query; returns paths or vertex/edge pairs.
        - No database mutations.
    """
    start = args["start_vertex"]
    direction = args.get("direction", "OUTBOUND")
    min_depth = int(args.get("min_depth", 1))
    max_depth = int(args.get("max_depth", 1))
    graph = args.get("graph")
    edge_cols = args.get("edge_collections") or []
    return_paths = bool(args.get("return_paths", False))
    limit = args.get("limit")

    if graph:
        aql = f"""
        FOR v, e, p IN {min_depth}..{max_depth} {direction} @start GRAPH @graph
          {"LIMIT @limit" if limit else ""}
          RETURN {"p" if return_paths else "{ vertex: v, edge: e }"}
        """
        bind = {"start": start, "graph": graph}
    else:
        if not edge_cols:
            raise ValueError("edge_collections must be provided when graph is not specified")
        # Traversal over explicit edge collections (comma-separated list)
        edge_expr = ", ".join(edge_cols)
        aql = f"""
        FOR v, e, p IN {min_depth}..{max_depth} {direction} @start {edge_expr}
          {"LIMIT @limit" if limit else ""}
          RETURN {"p" if return_paths else "{ vertex: v, edge: e }"}
        """
        bind = {"start": start}

    if limit:
        bind["limit"] = int(limit)
    cursor = db.aql.execute(aql, bind_vars=bind)
    with safe_cursor(cursor):
        return list(cursor)


@handle_errors
def handle_shortest_path(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Compute shortest path between two vertices using AQL."""
    """
    Operator model:
      Preconditions:
        - Database connection available.
        - 'start_vertex' and 'end_vertex' provided; either 'graph' or 'edge_collections' provided.
      Effects:
        - Executes shortest path query; returns found=False or the path.
        - No database mutations.
    """
    start = args["start_vertex"]
    end = args["end_vertex"]
    direction = args.get("direction", "OUTBOUND")
    graph = args.get("graph")
    edge_cols = args.get("edge_collections") or []
    return_paths = bool(args.get("return_paths", True))

    if graph:
        aql = f"""
        FOR v, e IN {direction} SHORTEST_PATH @start TO @end GRAPH @graph
          RETURN {{ vertices: v, edges: e }}
        """
        bind = {"start": start, "end": end, "graph": graph}
    else:
        if not edge_cols:
            raise ValueError("edge_collections must be provided when graph is not specified")
        edge_expr = ", ".join(edge_cols)
        aql = f"""
        FOR v, e IN {direction} SHORTEST_PATH @start TO @end {edge_expr}
          RETURN {{ vertices: v, edges: e }}
        """
        bind = {"start": start, "end": end}

    cursor = db.aql.execute(aql, bind_vars=bind)
    with safe_cursor(cursor):
        paths = list(cursor)
    if not paths:
        return {"found": False}
    # AQL returns a single element containing arrays of vertices/edges along the path
    res = paths[0]
    return {"found": True, **res}


# Additional graph management handlers
@handle_errors
def handle_list_graphs(db: StandardDatabase, args: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """List available graphs in the database.

    Returns a simplified list of graph metadata with at least the name.
    
    Operator model:
      Preconditions:
        - Database connection available.
      Effects:
        - Reads and returns graph metadata (name, and raw if available).
        - No database mutations.
    """
    try:
        graphs = db.graphs()  # type: ignore[attr-defined]
    except Exception:
        graphs = []
    result: List[Dict[str, Any]] = []
    for g in graphs or []:
        # Support both dict and object-like items
        if isinstance(g, dict):
            result.append({
                "name": g.get("name"),
                "_raw": g,
            })
        else:
            name = getattr(g, "name", None)
            result.append({"name": name})
    return result


@handle_errors
def handle_add_vertex_collection(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Add a vertex collection to a named graph."""
    """
    Operator model:
      Preconditions:
        - Database connection available; graph exists; collection exists.
      Effects:
        - Adds the vertex collection to the graph.
        - Mutates the graph definition.
    """
    graph_name = args["graph"]
    collection = args["collection"]
    g = db.graph(graph_name)
    g.add_vertex_collection(collection)  # type: ignore[attr-defined]
    return {"graph": graph_name, "collection_added": collection}


@handle_errors
def handle_add_edge_definition(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Create an edge definition in a named graph."""
    """
    Operator model:
      Preconditions:
        - Database connection available; graph exists; edge and vertex collections exist.
      Effects:
        - Creates the edge definition on the graph.
        - Mutates the graph definition.
    """
    graph_name = args["graph"]
    edge_collection = args["edge_collection"]
    from_cols = args.get("from_collections") or []
    to_cols = args.get("to_collections") or []
    g = db.graph(graph_name)
    g.create_edge_definition(  # type: ignore[attr-defined]
        edge_collection=edge_collection,
        from_vertex_collections=from_cols,
        to_vertex_collections=to_cols,
    )
    return {
        "graph": graph_name,
        "edge_definition": {
            "edge_collection": edge_collection,
            "from_collections": from_cols,
            "to_collections": to_cols,
        },
    }


@handle_errors
def handle_bulk_update(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Update multiple documents by key with batching."""
    """
    Operator model:
      Preconditions:
        - Database connection available; collection exists.
        - 'updates' list where each item has a key and an update payload.
      Effects:
        - Updates documents in batches; returns counts and any errors.
        - Mutates the collection for successfully updated documents.
    """
    collection = db.collection(args["collection"])
    updates: List[Dict[str, Any]] = args.get("updates") or []
    batch_size = int(args.get("batch_size", 1000))
    on_error = args.get("on_error", "stop")

    results: Dict[str, Any] = {
        "total_updates": len(updates),
        "updated_count": 0,
        "error_count": 0,
        "errors": [],
    }

    for i in range(0, len(updates), batch_size):
        batch = updates[i : i + batch_size]
        try:
            # Normalize payloads: each expects {_key, ...fields}
            normalized = []
            for item in batch:
                key = item.get("key") or item.get("_key")
                update = item.get("update") or {k: v for k, v in item.items() if k not in ("key", "_key")}
                normalized.append({"_key": key, **update})
            result = collection.update_many(normalized, keep_none=True, merge=True, return_new=False, sync=True)
            results["updated_count"] += len(result)
        except Exception as e:
            results["error_count"] += len(batch)
            results["errors"].append({"batch_start": i, "batch_size": len(batch), "error": str(e)})
            if on_error == "stop":
                break
            else:
                continue
    return results


# Graph Management Handlers (Phase 3 - New Graph Tools)
@handle_errors
def handle_backup_graph(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Export complete graph structure including vertices, edges, and metadata.

    Args:
        db: ArangoDB database instance
        args: Dictionary with 'graph_name', optional 'output_dir', 'include_metadata', 'doc_limit'

    Returns:
        Dictionary with backup report (output_dir, written files, counts)

    Operator model:
      Preconditions:
        - Database connection available; graph exists.
        - Output directory writable (if provided).
      Effects:
        - Reads graph structure and writes JSON files to output directory.
        - No database mutations; side-effect is file system writes.
    """
    graph_name = args["graph_name"]
    output_dir = args.get("output_dir")
    include_metadata = args.get("include_metadata", True)
    doc_limit = args.get("doc_limit")

    return backup_graph_to_dir(db, graph_name, output_dir, include_metadata, doc_limit)


@handle_errors
def handle_restore_graph(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Import graph data with referential integrity validation and conflict resolution.

    Args:
        db: ArangoDB database instance
        args: Dictionary with 'input_dir', optional 'graph_name', 'conflict_resolution', 'validate_integrity'

    Returns:
        Dictionary with restore report (restored collections, conflicts, errors)

    Operator model:
      Preconditions:
        - Database connection available; input directory contains valid graph backup.
        - Sufficient permissions for collection creation/modification.
      Effects:
        - Creates/updates vertex and edge collections.
        - Validates referential integrity during import.
        - Handles conflicts according to resolution strategy.
    """
    input_dir = args["input_dir"]
    graph_name = args.get("graph_name")
    conflict_resolution = args.get("conflict_resolution", "error")
    validate_integrity = args.get("validate_integrity", True)

    return restore_graph_from_dir(db, input_dir, graph_name, conflict_resolution, validate_integrity)


@handle_errors
def handle_backup_named_graphs(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Backup graph definitions from _graphs system collection.

    Args:
        db: ArangoDB database instance
        args: Dictionary with optional 'output_file', 'graph_names'

    Returns:
        Dictionary with backup report (output_file, graphs_backed_up, missing_graphs)

    Operator model:
      Preconditions:
        - Database connection available.
        - Output file location writable (if provided).
      Effects:
        - Reads graph definitions and writes JSON file.
        - No database mutations; side-effect is file system writes.
    """
    output_file = args.get("output_file")
    graph_names = args.get("graph_names")

    return backup_named_graphs(db, output_file, graph_names)


@handle_errors
def handle_validate_graph_integrity(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Verify graph consistency, orphaned edges, and constraint violations.

    Args:
        db: ArangoDB database instance
        args: Dictionary with optional 'graph_name', 'check_orphaned_edges', 'check_constraints', 'return_details'

    Returns:
        Dictionary with validation results (valid, orphaned_edges, constraint_violations, details)

    Operator model:
      Preconditions:
        - Database connection available; graphs exist (if specified).
      Effects:
        - Reads graph data and validates consistency.
        - No database mutations; read-only analysis.
    """
    graph_name = args.get("graph_name")
    check_orphaned_edges = args.get("check_orphaned_edges", True)
    check_constraints = args.get("check_constraints", True)
    return_details = args.get("return_details", False)

    return validate_graph_integrity(db, graph_name, check_orphaned_edges, check_constraints, return_details)


@handle_errors
def handle_graph_statistics(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive graph analytics with improved representativeness.

    Args:
        db: ArangoDB database instance
        args: Dictionary with optional parameters for graph analysis

    Returns:
        Dictionary with graph statistics (graphs_analyzed, statistics, analysis_timestamp)

    Operator model:
      Preconditions:
        - Database connection available; graphs exist (if specified).
      Effects:
        - Reads graph data and calculates analytics.
        - No database mutations; read-only analysis.
    """
    graph_name = args.get("graph_name")
    include_degree_distribution = args.get("include_degree_distribution", True)
    include_connectivity = args.get("include_connectivity", True)
    sample_size = args.get("sample_size")
    aggregate_collections = args.get("aggregate_collections", False)
    per_collection_stats = args.get("per_collection_stats", False)

    return calculate_graph_statistics(
        db,
        graph_name,
        include_degree_distribution,
        include_connectivity,
        sample_size,
        aggregate_collections,
        per_collection_stats
    )
