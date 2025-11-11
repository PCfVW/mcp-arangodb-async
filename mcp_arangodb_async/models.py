"""
ArangoDB MCP Server - Pydantic Models

Purpose:
    Defines Pydantic models used to validate inputs for all MCP tools. Models
    provide strict type checking, helpful error messages, and JSON schema
    generation for tool metadata.

Classes by category:

Core Data:
    - QueryArgs
    - ListCollectionsArgs
    - InsertArgs
    - UpdateArgs
    - RemoveArgs
    - CreateCollectionArgs
    - BackupArgs

Indexing & Query Analysis:
    - ListIndexesArgs
    - CreateIndexArgs
    - DeleteIndexArgs
    - ExplainQueryArgs

Validation & Bulk Ops:
    - ValidateReferencesArgs
    - InsertWithValidationArgs
    - BulkInsertArgs
    - BulkUpdateArgs

Graph:
    - EdgeDefinition
    - CreateGraphArgs
    - AddEdgeArgs
    - TraverseArgs
    - ShortestPathArgs
    - ListGraphsArgs
    - AddVertexCollectionArgs
    - AddEdgeDefinitionArgs

Schema Management:
    - CreateSchemaArgs
    - ValidateDocumentArgs

Enhanced Query:
    - QueryFilter
    - QuerySort
    - QueryBuilderArgs
    - QueryProfileArgs
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class QueryArgs(BaseModel):
    query: str = Field(description="AQL query string")
    bind_vars: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional bind variables for the AQL query"
    )


class ListCollectionsArgs(BaseModel):
    pass


class InsertArgs(BaseModel):
    collection: str
    document: Dict[str, Any]


class UpdateArgs(BaseModel):
    collection: str = Field(description="Name of the collection containing the document")
    key: str = Field(description="Document key to update")
    update: Dict[str, Any] = Field(description="Fields to update in the document")


class RemoveArgs(BaseModel):
    collection: str = Field(description="Name of the collection containing the document")
    key: str = Field(description="Document key to remove")


class CreateCollectionArgs(BaseModel):
    name: str = Field(description="Name of the collection to create")
    type: Literal["document", "edge"] = Field(default="document", description="Type of collection (document or edge)")
    waitForSync: Optional[bool] = Field(default=None, description="Whether to wait for sync to disk")


class BackupArgs(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    output_dir: Optional[str] = Field(
        default=None,
        alias="outputDir",
        description="Directory to write backup files (defaults to timestamped backups/ folder)"
    )
    collection: Optional[str] = Field(
        default=None,
        description="Single collection to backup (for TypeScript compatibility)"
    )
    collections: Optional[List[str]] = Field(
        default=None,
        description="List of collections to backup (if not specified, backs up all non-system collections)"
    )
    doc_limit: Optional[int] = Field(
        default=None,
        ge=1,
        alias="docLimit",
        description="Maximum number of documents to backup per collection"
    )


IndexType = Literal["persistent", "hash", "skiplist", "ttl", "fulltext", "geo"]


class ListIndexesArgs(BaseModel):
    collection: str = Field(description="Collection name to list indexes for")


class CreateIndexArgs(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    collection: str = Field(description="Name of the collection to create index on")
    type: IndexType = Field(default="persistent", description="Type of index to create")
    fields: List[str] = Field(description="Field paths to index")
    unique: Optional[bool] = Field(default=False, description="Whether the index should enforce uniqueness")
    sparse: Optional[bool] = Field(default=False, description="Whether the index should be sparse (ignore null values)")
    deduplicate: Optional[bool] = Field(default=True, description="Whether to deduplicate index entries")
    name: Optional[str] = Field(default=None, description="Custom name for the index")
    inBackground: Optional[bool] = Field(default=None, alias="in_background", description="Whether to create index in background")
    # Extended fields for additional index types
    ttl: Optional[int] = Field(default=None, description="TTL seconds (expireAfter) for TTL index")
    expireAfter: Optional[int] = Field(default=None, description="Alias for ttl (expireAfter)")
    minLength: Optional[int] = Field(default=None, description="Minimum length for fulltext index")
    geoJson: Optional[bool] = Field(default=None, description="If true, fields are in GeoJSON format for geo index")


class DeleteIndexArgs(BaseModel):
    collection: str = Field(description="Name of the collection containing the index")
    id_or_name: str = Field(description="Index ID (e.g., collection/12345) or name to delete")


class ExplainQueryArgs(BaseModel):
    query: str
    bind_vars: Optional[Dict[str, Any]] = None
    suggest_indexes: bool = True
    max_plans: int = 1


class ValidateReferencesArgs(BaseModel):
    collection: str
    reference_fields: List[str]
    fix_invalid: bool = False


class InsertWithValidationArgs(BaseModel):
    collection: str
    document: Dict[str, Any]
    reference_fields: List[str] = Field(default_factory=list)


class BulkInsertArgs(BaseModel):
    collection: str
    documents: List[Dict[str, Any]]
    validate_refs: bool = False
    batch_size: int = 1000
    on_error: Literal["stop", "continue", "ignore"] = "stop"


class BulkUpdateArgs(BaseModel):
    collection: str
    updates: List[Dict[str, Any]]  # each must include key and update fields
    batch_size: int = 1000
    on_error: Literal["stop", "continue", "ignore"] = "stop"


# Graph models (Phase 2)
class EdgeDefinition(BaseModel):
    edge_collection: str
    from_collections: List[str]
    to_collections: List[str]


class CreateGraphArgs(BaseModel):
    name: str
    edge_definitions: List[EdgeDefinition]
    create_collections: bool = True


class AddEdgeArgs(BaseModel):
    collection: str
    from_id: str = Field(description="_from document id, e.g., users/123")
    to_id: str = Field(description="_to document id, e.g., orders/456")
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict)


class TraverseArgs(BaseModel):
    start_vertex: str
    direction: Literal["OUTBOUND", "INBOUND", "ANY"] = "OUTBOUND"
    min_depth: int = 1
    max_depth: int = 1
    graph: Optional[str] = None
    edge_collections: Optional[List[str]] = None
    return_paths: bool = False
    limit: Optional[int] = None


class ShortestPathArgs(BaseModel):
    start_vertex: str
    end_vertex: str
    direction: Literal["OUTBOUND", "INBOUND", "ANY"] = "OUTBOUND"
    graph: Optional[str] = None
    edge_collections: Optional[List[str]] = None
    return_paths: bool = True


# Additional graph management models
class ListGraphsArgs(BaseModel):
    pass


class AddVertexCollectionArgs(BaseModel):
    graph: str
    collection: str


class AddEdgeDefinitionArgs(BaseModel):
    graph: str
    edge_collection: str
    from_collections: List[str]
    to_collections: List[str]


# Schema management
class CreateSchemaArgs(BaseModel):
    name: str
    collection: str
    schema_def: Dict[str, Any] = Field(
        description="JSON Schema draft-07 compatible schema",
        validation_alias="schema",
        serialization_alias="schema",
    )


class ValidateDocumentArgs(BaseModel):
    collection: str
    document: Dict[str, Any]
    schema_name: Optional[str] = Field(default=None, description="Name of stored schema to use")
    schema_def: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Inline JSON Schema to validate against",
        validation_alias="schema",
        serialization_alias="schema",
    )


# Enhanced query tools
class QueryFilter(BaseModel):
    field: str
    op: Literal["==", "!=", "<", "<=", ">", ">=", "IN", "LIKE"]
    value: Any


class QuerySort(BaseModel):
    field: str
    direction: Literal["ASC", "DESC"] = "ASC"


class QueryBuilderArgs(BaseModel):
    collection: str
    filters: List[QueryFilter] = Field(default_factory=list)
    sort: List[QuerySort] = Field(default_factory=list)
    limit: Optional[int] = None
    return_fields: Optional[List[str]] = Field(default=None, description="Fields to project; omit for full doc")


class QueryProfileArgs(BaseModel):
    query: str
    bind_vars: Optional[Dict[str, Any]] = None
    max_plans: int = 1


# Graph Management Models (Phase 1 - New Graph Tools)
class BackupGraphArgs(BaseModel):
    """Arguments for backing up a complete graph structure."""
    model_config = ConfigDict(populate_by_name=True)

    graph_name: str = Field(
        description="Name of the graph to backup"
    )
    output_dir: Optional[str] = Field(
        default=None,
        alias="outputDir",
        description="Output directory for backup files (defaults to timestamped graph_backups/ folder)"
    )
    include_metadata: bool = Field(
        default=True,
        alias="includeMetadata",
        description="Include graph metadata and definitions in backup"
    )
    doc_limit: Optional[int] = Field(
        default=None,
        ge=1,
        alias="docLimit",
        description="Maximum number of documents to backup per collection"
    )


class RestoreGraphArgs(BaseModel):
    """Arguments for restoring a graph from backup."""
    model_config = ConfigDict(populate_by_name=True)

    input_dir: str = Field(
        alias="inputDir",
        description="Directory containing graph backup files"
    )
    graph_name: Optional[str] = Field(
        default=None,
        alias="graphName",
        description="Target graph name (defaults to original name from backup)"
    )
    conflict_resolution: Literal["skip", "overwrite", "error"] = Field(
        default="error",
        alias="conflictResolution",
        description="How to handle conflicts: skip existing, overwrite, or error"
    )
    validate_integrity: bool = Field(
        default=True,
        alias="validateIntegrity",
        description="Validate referential integrity during restore"
    )


class BackupNamedGraphsArgs(BaseModel):
    """Arguments for backing up graph definitions from _graphs collection."""
    model_config = ConfigDict(populate_by_name=True)

    output_file: Optional[str] = Field(
        default=None,
        alias="outputFile",
        description="Output file for graph definitions (defaults to timestamped file)"
    )
    graph_names: Optional[List[str]] = Field(
        default=None,
        alias="graphNames",
        description="Specific graphs to backup (if not specified, backs up all graphs)"
    )


class ValidateGraphIntegrityArgs(BaseModel):
    """Arguments for validating graph consistency and integrity."""
    model_config = ConfigDict(populate_by_name=True)

    graph_name: Optional[str] = Field(
        default=None,
        alias="graphName",
        description="Specific graph to validate (if not specified, validates all graphs)"
    )
    check_orphaned_edges: bool = Field(
        default=True,
        alias="checkOrphanedEdges",
        description="Check for edges with missing vertices"
    )
    check_constraints: bool = Field(
        default=True,
        alias="checkConstraints",
        description="Validate graph constraints and edge definitions"
    )
    return_details: bool = Field(
        default=False,
        alias="returnDetails",
        description="Return detailed violation information"
    )


class GraphStatisticsArgs(BaseModel):
    """Arguments for generating comprehensive graph analytics."""
    model_config = ConfigDict(populate_by_name=True)

    graph_name: Optional[str] = Field(
        default=None,
        alias="graphName",
        description="Specific graph to analyze (if not specified, analyzes all graphs)"
    )
    include_degree_distribution: bool = Field(
        default=True,
        alias="includeDegreeDistribution",
        description="Calculate degree distribution statistics"
    )
    include_connectivity: bool = Field(
        default=True,
        alias="includeConnectivity",
        description="Calculate connectivity metrics"
    )
    sample_size: Optional[int] = Field(
        default=None,
        ge=100,
        alias="sampleSize",
        description="Sample size for large graphs (defaults to automatic sizing)"
    )
    aggregate_collections: bool = Field(
        default=False,
        alias="aggregateCollections",
        description="Aggregate statistics across all collections for more representative results"
    )
    per_collection_stats: bool = Field(
        default=False,
        alias="perCollectionStats",
        description="Provide detailed per-collection statistics breakdown"
    )


class ArangoDatabaseStatusArgs(BaseModel):
    """Arguments for arango_database_status tool (no parameters required)."""
    pass


# Pattern 1: Progressive Tool Discovery
class SearchToolsArgs(BaseModel):
    """Arguments for arango_search_tools."""
    keywords: List[str] = Field(
        description="Keywords to search for in tool names and descriptions"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Filter by categories: core_data, indexing, validation, schema, query, graph_basic, graph_advanced, aliases, health"
    )
    detail_level: Literal["name", "summary", "full"] = Field(
        default="summary",
        description="Level of detail: 'name' (just names), 'summary' (names + descriptions), 'full' (complete schemas)"
    )


class ListToolsByCategoryArgs(BaseModel):
    """Arguments for arango_list_tools_by_category."""
    category: Optional[str] = Field(
        default=None,
        description="Category to filter by. If None, returns all categories with their tools."
    )


# Pattern 2: Context Switching
class SwitchContextArgs(BaseModel):
    """Arguments for arango_switch_context."""
    context: Literal[
        "baseline", "data_analysis", "graph_modeling",
        "bulk_operations", "schema_validation", "full"
    ] = Field(
        description="Workflow context to switch to"
    )


class GetActiveContextArgs(BaseModel):
    """Arguments for arango_get_active_context."""
    pass


class ListContextsArgs(BaseModel):
    """Arguments for arango_list_contexts."""
    include_tools: bool = Field(
        default=False,
        description="Include tool lists for each context"
    )


# Pattern 3: Tool Unloading
class AdvanceWorkflowStageArgs(BaseModel):
    """Arguments for arango_advance_workflow_stage."""
    stage: Literal["setup", "data_loading", "analysis", "cleanup"] = Field(
        description="Workflow stage to advance to"
    )


class GetToolUsageStatsArgs(BaseModel):
    """Arguments for arango_get_tool_usage_stats."""
    pass


class UnloadToolsArgs(BaseModel):
    """Arguments for arango_unload_tools."""
    tool_names: List[str] = Field(
        description="List of tool names to unload from active context"
    )
