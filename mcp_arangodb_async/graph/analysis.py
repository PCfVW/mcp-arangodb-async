"""Graph analysis operations."""

from __future__ import annotations

from typing import Any, Dict
from arango.database import StandardDatabase
from .graph_backup import validate_graph_integrity_core, calculate_graph_statistics_core


def validate_graph_integrity(
    db: StandardDatabase, args: Dict[str, Any]
) -> Dict[str, Any]:
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
    graph_name = args.get("graph_name") or args.get("graph")
    check_orphaned_edges = args.get("check_orphaned_edges", True)
    check_constraints = args.get("check_constraints", True)
    return_details = args.get("return_details", False)

    return validate_graph_integrity_core(
        db, graph_name, check_orphaned_edges, check_constraints, return_details
    )


def graph_statistics(
    db: StandardDatabase, args: Dict[str, Any]
) -> Dict[str, Any]:
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
    graph_name = args.get("graph_name") or args.get("graph")
    include_degree_distribution = args.get("include_degree_distribution", True)
    include_connectivity = args.get("include_connectivity", True)
    sample_size = args.get("sample_size")
    aggregate_collections = args.get("aggregate_collections", False)
    per_collection_stats = args.get("per_collection_stats", False)

    return calculate_graph_statistics_core(
        db,
        graph_name,
        include_degree_distribution,
        include_connectivity,
        sample_size,
        aggregate_collections,
        per_collection_stats,
    )
