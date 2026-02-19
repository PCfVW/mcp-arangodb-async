"""Pydantic models for collection operations (v4.0).

Purpose:
    Defines Pydantic v2 models for validating inputs to collection operations.
    Covers CRUD, batch operations, indexing, schema management, and backups.

Operations:
    CRUD:
    - insert: Insert a document into a collection
    - update: Update a document by key
    - remove: Remove a document by key
    - insert_with_validation: Insert with reference validation
    - list: List all collections

    Batch:
    - bulk_insert: Insert multiple documents
    - bulk_update: Update multiple documents

    Index:
    - list_indexes: List indexes for a collection
    - create_index: Create an index
    - delete_index: Delete an index

    Schema:
    - create_schema: Create/store a JSON Schema
    - validate_document: Validate a document against a schema
    - validate_references: Validate reference fields

    Management:
    - create: Create a new collection

    Backup:
    - backup: Backup collection data
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


IndexType = Literal["persistent", "hash", "skiplist", "ttl", "fulltext", "geo"]


class CollectionArgs(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: Literal[
        # CRUD
        "insert", "find", "update", "remove", "insert_with_validation", "list",
        # Batch
        "bulk_insert", "bulk_update", "import", "export",
        # Index
        "list_indexes", "create_index", "delete_index",
        # Schema
        "get_schema", "create_schema", "validate_document", "validate_references",
        # Management
        "create", "stats", "drop", "truncate",
        # Backup
        "backup"
    ] = Field(description="Collection operation to perform")


# CRUD Operations

class InsertArgs(BaseModel):
    """Arguments for insert operation."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    document: Dict[str, Any] = Field(description="Document to insert")
    database: Optional[str] = Field(default=None, description="Database override")


class FindArgs(BaseModel):
    """Arguments for find operation.

    Supports two modes:
    - By key: Provide 'key' parameter for direct document lookup
    - By filter: Provide 'filter' parameter with MongoDB-style operators
    """

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    key: Optional[str] = Field(
        default=None,
        description="Document key for direct lookup"
    )
    filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter criteria (supports $gt, $gte, $lt, $lte, $ne, $in operators)"
    )
    limit: Optional[int] = Field(
        default=100,
        ge=1,
        description="Maximum documents to return for filter queries"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class UpdateArgs(BaseModel):
    """Arguments for update operation."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    key: str = Field(description="Document key to update")
    update: Dict[str, Any] = Field(description="Fields to update")
    database: Optional[str] = Field(default=None, description="Database override")


class RemoveArgs(BaseModel):
    """Arguments for remove operation."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    key: str = Field(description="Document key to remove")
    database: Optional[str] = Field(default=None, description="Database override")


class InsertWithValidationArgs(BaseModel):
    """Arguments for insert_with_validation operation."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    document: Dict[str, Any] = Field(description="Document to insert")
    reference_fields: List[str] = Field(
        default_factory=list,
        description="Fields to validate as references"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class ListArgs(BaseModel):
    """Arguments for list operation (list collections)."""

    model_config = ConfigDict(extra="allow")

    database: Optional[str] = Field(default=None, description="Database override")


# Batch Operations

class BulkInsertArgs(BaseModel):
    """Arguments for bulk_insert operation."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    documents: List[Dict[str, Any]] = Field(description="Documents to insert")
    batch_size: int = Field(
        default=1000,
        ge=1,
        description="Batch size for insertion"
    )
    on_error: Literal["stop", "continue", "ignore"] = Field(
        default="stop",
        description="Error handling mode"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class BulkUpdateArgs(BaseModel):
    """Arguments for bulk_update operation."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    updates: List[Dict[str, Any]] = Field(
        description="Update documents (each must have 'key' and update fields)"
    )
    batch_size: int = Field(
        default=1000,
        ge=1,
        description="Batch size for updates"
    )
    on_error: Literal["stop", "continue", "ignore"] = Field(
        default="stop",
        description="Error handling mode"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class ImportArgs(BaseModel):
    """Arguments for import operation.

    Reads file content and creates a document, with optional upsert.
    If document has '_key' field, performs upsert; otherwise inserts new document.
    """

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    file_path: str = Field(description="Path to file to import")
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Import options (title, source, weight, tags, etc.)"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class ExportArgs(BaseModel):
    """Arguments for export operation.

    Exports documents to file(s) by key or filter criteria.
    Supports MongoDB-style filter operators ($gt, $gte, $lt, $lte, $ne, $in).
    """

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    key: Optional[str] = Field(
        default=None,
        description="Document key for single document export"
    )
    filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter criteria for batch export"
    )
    options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Export options (output_dir, limit)"
    )
    database: Optional[str] = Field(default=None, description="Database override")


# Index Operations

class ListIndexesArgs(BaseModel):
    """Arguments for list_indexes operation."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    database: Optional[str] = Field(default=None, description="Database override")


class CreateIndexArgs(BaseModel):
    """Arguments for create_index operation."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    collection: str = Field(description="Name of the collection")
    type: IndexType = Field(
        default="persistent",
        description="Type of index to create"
    )
    fields: List[str] = Field(description="Field paths to index")
    unique: Optional[bool] = Field(
        default=False,
        description="Enforce uniqueness"
    )
    sparse: Optional[bool] = Field(
        default=False,
        description="Sparse index (ignore null values)"
    )
    deduplicate: Optional[bool] = Field(
        default=True,
        description="Deduplicate index entries"
    )
    name: Optional[str] = Field(
        default=None,
        description="Custom index name"
    )
    in_background: Optional[bool] = Field(
        default=None,
        alias="inBackground",
        description="Create index in background"
    )
    ttl: Optional[int] = Field(
        default=None,
        description="TTL seconds for TTL index"
    )
    min_length: Optional[int] = Field(
        default=None,
        alias="minLength",
        description="Minimum length for fulltext index"
    )
    geo_json: Optional[bool] = Field(
        default=None,
        alias="geoJson",
        description="GeoJSON format for geo index"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class DeleteIndexArgs(BaseModel):
    """Arguments for delete_index operation."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    id_or_name: str = Field(
        description="Index ID (e.g., collection/12345) or name to delete"
    )
    database: Optional[str] = Field(default=None, description="Database override")


# Schema Operations

class GetSchemaArgs(BaseModel):
    """Arguments for get_schema operation.

    Retrieves stored JSON Schema for a collection.
    """

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    schema_name: Optional[str] = Field(
        default="default",
        description="Name of stored schema to retrieve"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class CreateSchemaArgs(BaseModel):
    """Arguments for create_schema operation."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    name: str = Field(description="Schema name")
    collection: str = Field(description="Associated collection")
    schema_def: Dict[str, Any] = Field(
        description="JSON Schema draft-07 compatible schema",
        alias="schema"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class ValidateDocumentArgs(BaseModel):
    """Arguments for validate_document operation."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    collection: str = Field(description="Name of the collection")
    document: Dict[str, Any] = Field(description="Document to validate")
    schema_name: Optional[str] = Field(
        default=None,
        description="Name of stored schema to use"
    )
    schema_def: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Inline JSON Schema to validate against",
        alias="schema"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class ValidateReferencesArgs(BaseModel):
    """Arguments for validate_references operation."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    reference_fields: List[str] = Field(
        description="Fields to validate as references"
    )
    fix_invalid: bool = Field(
        default=False,
        description="Fix invalid references"
    )
    database: Optional[str] = Field(default=None, description="Database override")


# Management Operations

class CreateArgs(BaseModel):
    """Arguments for create operation (create collection)."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Name of the collection to create")
    type: Literal["document", "edge"] = Field(
        default="document",
        description="Collection type"
    )
    wait_for_sync: Optional[bool] = Field(
        default=None,
        alias="waitForSync",
        description="Wait for sync to disk"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class StatsArgs(BaseModel):
    """Arguments for stats operation.

    Retrieves collection statistics including document count, type, and configuration.
    """

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection")
    database: Optional[str] = Field(default=None, description="Database override")


class DropArgs(BaseModel):
    """Arguments for drop operation.

    Deletes a collection and all its documents from the database.
    This operation is irreversible.
    """

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection to drop")
    database: Optional[str] = Field(default=None, description="Database override")


class TruncateArgs(BaseModel):
    """Arguments for truncate operation.

    Removes all documents from a collection while keeping its structure,
    indexes, and schema intact.
    """

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the collection to truncate")
    database: Optional[str] = Field(default=None, description="Database override")


# Backup Operations

class BackupArgs(BaseModel):
    """Arguments for backup operation."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    output_dir: Optional[str] = Field(
        default=None,
        alias="outputDir",
        description="Directory for backup files"
    )
    collection: Optional[str] = Field(
        default=None,
        description="Single collection to backup"
    )
    collections: Optional[List[str]] = Field(
        default=None,
        description="List of collections to backup"
    )
    doc_limit: Optional[int] = Field(
        default=None,
        ge=1,
        alias="docLimit",
        description="Max documents per collection"
    )
    database: Optional[str] = Field(default=None, description="Database override")
