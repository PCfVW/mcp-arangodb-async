"""Pydantic models for graph operations (v4.0).

Purpose:
    Defines Pydantic v2 models for validating inputs to graph operations.
    Covers graph management, edge operations, traversal, backup/restore, and analysis.

Operations:
    Management:
    - create: Create a new graph
    - list: List all graphs
    - add_vertex_collection: Add a vertex collection to a graph
    - add_edge_definition: Add edge definition to a graph

    Edge:
    - add_edge: Add an edge between vertices

    Traversal:
    - traverse: Traverse a graph from a starting vertex
    - shortest_path: Find shortest path between vertices

    Backup:
    - backup: Backup a complete graph
    - restore: Restore a graph from backup
    - backup_named: Backup graph definitions

    Analysis:
    - validate_integrity: Validate graph integrity
    - statistics: Generate graph statistics
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class GraphArgs(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: Literal[
        # Management
        "create", "list", "add_vertex_collection", "add_edge_definition",
        # Edge
        "add_edge",
        # Traversal
        "traverse", "shortest_path",
        # Backup
        "backup", "restore", "backup_named",
        # Analysis
        "validate_integrity", "statistics"
    ] = Field(description="Graph operation to perform")


# Management Operations

class EdgeDefinition(BaseModel):
    """Edge definition for graph creation."""

    edge_collection: str = Field(description="Name of the edge collection")
    from_collections: List[str] = Field(description="Source vertex collections")
    to_collections: List[str] = Field(description="Target vertex collections")


class CreateArgs(BaseModel):
    """Arguments for create operation (create graph)."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Name of the graph")
    edge_definitions: List[EdgeDefinition] = Field(
        description="Edge definitions for the graph"
    )
    create_collections: bool = Field(
        default=True,
        description="Whether to create collections if they don't exist"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class ListArgs(BaseModel):
    """Arguments for list operation (list graphs)."""

    model_config = ConfigDict(extra="allow")

    database: Optional[str] = Field(default=None, description="Database override")


class AddVertexCollectionArgs(BaseModel):
    """Arguments for add_vertex_collection operation."""

    model_config = ConfigDict(extra="allow")

    graph: str = Field(description="Name of the graph")
    collection: str = Field(description="Name of the vertex collection to add")
    database: Optional[str] = Field(default=None, description="Database override")


class AddEdgeDefinitionArgs(BaseModel):
    """Arguments for add_edge_definition operation."""

    model_config = ConfigDict(extra="allow")

    graph: str = Field(description="Name of the graph")
    edge_collection: str = Field(description="Name of the edge collection")
    from_collections: List[str] = Field(description="Source vertex collections")
    to_collections: List[str] = Field(description="Target vertex collections")
    database: Optional[str] = Field(default=None, description="Database override")


# Edge Operations

class AddEdgeArgs(BaseModel):
    """Arguments for add_edge operation."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Name of the edge collection")
    from_id: str = Field(
        description="Source document ID (e.g., users/123)"
    )
    to_id: str = Field(
        description="Target document ID (e.g., orders/456)"
    )
    attributes: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional edge attributes"
    )
    database: Optional[str] = Field(default=None, description="Database override")


# Traversal Operations

class TraverseArgs(BaseModel):
    """Arguments for traverse operation."""

    model_config = ConfigDict(extra="allow")

    start_vertex: str = Field(description="Starting vertex ID")
    direction: Literal["OUTBOUND", "INBOUND", "ANY"] = Field(
        default="OUTBOUND",
        description="Traversal direction"
    )
    min_depth: int = Field(
        default=1,
        ge=0,
        description="Minimum traversal depth"
    )
    max_depth: int = Field(
        default=1,
        ge=0,
        description="Maximum traversal depth"
    )
    graph: Optional[str] = Field(
        default=None,
        description="Graph name (optional)"
    )
    edge_collections: Optional[List[str]] = Field(
        default=None,
        description="Specific edge collections to traverse"
    )
    return_paths: bool = Field(
        default=False,
        description="Return full traversal paths"
    )
    limit: Optional[int] = Field(
        default=None,
        ge=1,
        description="Limit number of results"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class ShortestPathArgs(BaseModel):
    """Arguments for shortest_path operation."""

    model_config = ConfigDict(extra="allow")

    start_vertex: str = Field(description="Starting vertex ID")
    end_vertex: str = Field(description="Ending vertex ID")
    direction: Literal["OUTBOUND", "INBOUND", "ANY"] = Field(
        default="OUTBOUND",
        description="Path direction"
    )
    graph: Optional[str] = Field(
        default=None,
        description="Graph name (optional)"
    )
    edge_collections: Optional[List[str]] = Field(
        default=None,
        description="Specific edge collections to use"
    )
    return_paths: bool = Field(
        default=True,
        description="Return full path details"
    )
    database: Optional[str] = Field(default=None, description="Database override")


# Backup Operations

class BackupArgs(BaseModel):
    """Arguments for backup operation (backup graph)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    graph_name: str = Field(description="Name of the graph to backup")
    output_dir: Optional[str] = Field(
        default=None,
        alias="outputDir",
        description="Output directory for backup files"
    )
    include_metadata: bool = Field(
        default=True,
        alias="includeMetadata",
        description="Include graph metadata and definitions"
    )
    doc_limit: Optional[int] = Field(
        default=None,
        ge=1,
        alias="docLimit",
        description="Max documents per collection"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class RestoreArgs(BaseModel):
    """Arguments for restore operation (restore graph from backup)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    input_dir: str = Field(
        alias="inputDir",
        description="Directory containing backup files"
    )
    graph_name: Optional[str] = Field(
        default=None,
        alias="graphName",
        description="Target graph name"
    )
    conflict_resolution: Literal["skip", "overwrite", "error"] = Field(
        default="error",
        alias="conflictResolution",
        description="Conflict resolution strategy"
    )
    validate_integrity: bool = Field(
        default=True,
        alias="validateIntegrity",
        description="Validate integrity during restore"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class BackupNamedArgs(BaseModel):
    """Arguments for backup_named operation (backup graph definitions)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    output_file: Optional[str] = Field(
        default=None,
        alias="outputFile",
        description="Output file for graph definitions"
    )
    graph_names: Optional[List[str]] = Field(
        default=None,
        alias="graphNames",
        description="Specific graphs to backup"
    )
    database: Optional[str] = Field(default=None, description="Database override")


# Analysis Operations

class ValidateIntegrityArgs(BaseModel):
    """Arguments for validate_integrity operation."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    graph_name: Optional[str] = Field(
        default=None,
        alias="graphName",
        description="Specific graph to validate"
    )
    check_orphaned_edges: bool = Field(
        default=True,
        alias="checkOrphanedEdges",
        description="Check for orphaned edges"
    )
    check_constraints: bool = Field(
        default=True,
        alias="checkConstraints",
        description="Validate constraints"
    )
    return_details: bool = Field(
        default=False,
        alias="returnDetails",
        description="Return detailed violation information"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class StatisticsArgs(BaseModel):
    """Arguments for statistics operation (graph statistics)."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    graph_name: Optional[str] = Field(
        default=None,
        alias="graphName",
        description="Specific graph to analyze"
    )
    include_degree_distribution: bool = Field(
        default=True,
        alias="includeDegreeDistribution",
        description="Calculate degree distribution"
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
        description="Sample size for large graphs"
    )
    aggregate_collections: bool = Field(
        default=False,
        alias="aggregateCollections",
        description="Aggregate stats across collections"
    )
    per_collection_stats: bool = Field(
        default=False,
        alias="perCollectionStats",
        description="Provide per-collection breakdown"
    )
    database: Optional[str] = Field(default=None, description="Database override")
