"""
ArangoDB MCP Server - Graph Backup Utilities

This module provides specialized functionality to backup and restore ArangoDB graphs,
including complete graph structures, graph definitions, integrity validation, and analytics.

Functions:
- backup_graph_to_dir() - Export complete graph structure to directory
- restore_graph_from_dir() - Import graph data with integrity validation
- backup_named_graphs() - Backup graph definitions from _graphs collection
- validate_graph_integrity() - Validate graph consistency and constraints
- calculate_graph_statistics() - Generate comprehensive graph analytics

API Convention Note:
The python-arango library returns graph properties with snake_case keys (not camelCase).
Key graph property fields:
  - edge_definitions: list of edge collection definitions
  - edge_collection: name of the edge collection
  - from_vertex_collections: list of source vertex collections
  - to_vertex_collections: list of target vertex collections
  - orphan_collections: vertex collections without edges
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from arango.database import StandardDatabase
from arango.exceptions import ArangoError

from .backup import validate_output_directory


def backup_graph_to_dir(
    db: StandardDatabase, 
    graph_name: str, 
    output_dir: Optional[str] = None, 
    include_metadata: bool = True, 
    doc_limit: Optional[int] = None
) -> Dict[str, Any]:
    """Export complete graph structure to directory.
    
    Creates structured backup with:
    - graph_metadata.json: Graph definition and edge definitions
    - vertices/: Directory with vertex collection JSON files
    - edges/: Directory with edge collection JSON files
    - backup_report.json: Summary report
    
    Args:
        db: ArangoDB database instance
        graph_name: Name of the graph to backup
        output_dir: Output directory (defaults to timestamped folder)
        include_metadata: Include graph metadata in backup
        doc_limit: Maximum documents per collection
        
    Returns:
        Dictionary with backup report
        
    Raises:
        ValueError: If graph doesn't exist or output directory invalid
        ArangoError: If database operations fail
    """
    # Validate graph exists
    if not db.has_graph(graph_name):
        raise ValueError(f"Graph '{graph_name}' does not exist")
    
    # Setup output directory
    if output_dir is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("graph_backups", f"{graph_name}_{ts}")
    
    output_dir = validate_output_directory(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    # Get graph metadata
    graph = db.graph(graph_name)
    graph_info = graph.properties()

    # Extract collections from edge definitions
    vertex_collections = set()
    edge_collections = set()

    # API Convention: python-arango returns snake_case keys (not camelCase)
    # Graph properties structure:
    #   - edge_definitions: list of edge collection definitions
    #   - edge_collection: name of the edge collection
    #   - from_vertex_collections: list of source vertex collections
    #   - to_vertex_collections: list of target vertex collections
    #   - orphan_collections: vertex collections without edges
    for edge_def in graph_info.get("edge_definitions", []):
        edge_collections.add(edge_def["edge_collection"])
        vertex_collections.update(edge_def.get("from_vertex_collections", []))
        vertex_collections.update(edge_def.get("to_vertex_collections", []))

    # Add orphan collections (vertex collections not connected by edges)
    vertex_collections.update(graph_info.get("orphan_collections", []))
    
    # Backup vertex collections
    vertex_dir = os.path.join(output_dir, "vertices")
    os.makedirs(vertex_dir, exist_ok=True)
    vertex_files = []
    
    for col_name in vertex_collections:
        if db.has_collection(col_name):
            file_path = os.path.join(vertex_dir, f"{col_name}.json")
            count = _backup_collection_to_file(db, col_name, file_path, doc_limit)
            vertex_files.append({"collection": col_name, "path": file_path, "count": count})
    
    # Backup edge collections  
    edge_dir = os.path.join(output_dir, "edges")
    os.makedirs(edge_dir, exist_ok=True)
    edge_files = []
    
    for col_name in edge_collections:
        if db.has_collection(col_name):
            file_path = os.path.join(edge_dir, f"{col_name}.json")
            count = _backup_collection_to_file(db, col_name, file_path, doc_limit)
            edge_files.append({"collection": col_name, "path": file_path, "count": count})
    
    # Save metadata
    if include_metadata:
        metadata_path = os.path.join(output_dir, "graph_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump({
                "graph_name": graph_name,
                "graph_properties": graph_info,
                "backup_timestamp": datetime.now().isoformat(),
                "vertex_collections": list(vertex_collections),
                "edge_collections": list(edge_collections),
            }, f, indent=2, ensure_ascii=False)
    
    # Create backup report
    report = {
        "graph_name": graph_name,
        "output_dir": output_dir,
        "vertex_files": vertex_files,
        "edge_files": edge_files,
        "total_vertex_collections": len(vertex_files),
        "total_edge_collections": len(edge_files),
        "total_documents": sum(f["count"] for f in vertex_files + edge_files),
        "metadata_included": include_metadata,
    }
    
    # Save report
    report_path = os.path.join(output_dir, "backup_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report


def _backup_collection_to_file(
    db: StandardDatabase, 
    collection_name: str, 
    file_path: str, 
    doc_limit: Optional[int] = None
) -> int:
    """Helper to backup single collection to JSON file.
    
    Args:
        db: Database instance
        collection_name: Name of collection to backup
        file_path: Output file path
        doc_limit: Maximum documents to backup
        
    Returns:
        Number of documents backed up
    """
    col = db.collection(collection_name)
    cursor = col.all()
    count = 0
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write('[')
            first_doc = True
            
            for i, doc in enumerate(cursor):
                if doc_limit is not None and i >= doc_limit:
                    break
                
                if not first_doc:
                    f.write(',')
                f.write('\n  ')
                json.dump(doc, f, ensure_ascii=False)
                first_doc = False
                count += 1
            
            f.write('\n]')
    finally:
        if hasattr(cursor, 'close'):
            try:
                cursor.close()
            except Exception:
                pass  # Ignore cleanup errors
    
    return count


def backup_named_graphs(
    db: StandardDatabase, 
    output_file: Optional[str] = None,
    graph_names: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Backup graph definitions from _graphs system collection.
    
    Args:
        db: Database instance
        output_file: Output file path (defaults to timestamped file)
        graph_names: Specific graphs to backup (all if None)
        
    Returns:
        Dictionary with backup report
    """
    # Default output file
    if output_file is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"named_graphs_backup_{ts}.json"
    
    output_file = os.path.abspath(output_file)
    
    # Get all graph definitions
    all_graphs = list(db.graphs())
    
    # Filter by requested graph names
    if graph_names:
        graphs_to_backup = [g for g in all_graphs if g["name"] in graph_names]
        missing_graphs = set(graph_names) - {g["name"] for g in graphs_to_backup}
    else:
        graphs_to_backup = all_graphs
        missing_graphs = set()
    
    # Create backup data
    backup_data = {
        "backup_timestamp": datetime.now().isoformat(),
        "total_graphs": len(graphs_to_backup),
        "graphs": graphs_to_backup,
        "missing_graphs": list(missing_graphs) if missing_graphs else [],
    }
    
    # Write backup file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    return {
        "output_file": output_file,
        "graphs_backed_up": len(graphs_to_backup),
        "missing_graphs": list(missing_graphs),
        "backup_size_bytes": os.path.getsize(output_file),
    }


def restore_graph_from_dir(
    db: StandardDatabase,
    input_dir: str,
    graph_name: Optional[str] = None,
    conflict_resolution: str = "error",
    validate_integrity: bool = True
) -> Dict[str, Any]:
    """Import graph data with integrity validation and conflict resolution.

    Args:
        db: Database instance
        input_dir: Directory containing graph backup files
        graph_name: Target graph name (defaults to original)
        conflict_resolution: How to handle conflicts ("skip", "overwrite", "error")
        validate_integrity: Whether to validate integrity after restore

    Returns:
        Dictionary with restore report

    Raises:
        ValueError: If input directory invalid or backup corrupted
        ArangoError: If database operations fail
    """
    # Validate input directory structure
    input_dir = os.path.abspath(input_dir)
    if not os.path.exists(input_dir):
        raise ValueError(f"Input directory '{input_dir}' does not exist")

    metadata_path = os.path.join(input_dir, "graph_metadata.json")
    if not os.path.exists(metadata_path):
        raise ValueError("Invalid backup: graph_metadata.json not found")

    # Load metadata
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    original_graph_name = metadata["graph_name"]
    target_graph_name = graph_name or original_graph_name
    graph_properties = metadata["graph_properties"]

    # Track restoration progress
    restored_vertices = []
    restored_edges = []
    conflicts = []
    errors = []

    # Restore vertex collections first
    vertex_dir = os.path.join(input_dir, "vertices")
    if os.path.exists(vertex_dir):
        for vertex_file in os.listdir(vertex_dir):
            if vertex_file.endswith(".json"):
                col_name = vertex_file[:-5]  # Remove .json
                file_path = os.path.join(vertex_dir, vertex_file)

                try:
                    result = _restore_collection_from_file(db, col_name, file_path, conflict_resolution)
                    restored_vertices.append(result)
                except Exception as e:
                    errors.append({"collection": col_name, "error": str(e), "type": "vertex"})

    # Restore edge collections
    edge_dir = os.path.join(input_dir, "edges")
    if os.path.exists(edge_dir):
        for edge_file in os.listdir(edge_dir):
            if edge_file.endswith(".json"):
                col_name = edge_file[:-5]
                file_path = os.path.join(edge_dir, edge_file)

                try:
                    result = _restore_collection_from_file(db, col_name, file_path, conflict_resolution)
                    restored_edges.append(result)
                except Exception as e:
                    errors.append({"collection": col_name, "error": str(e), "type": "edge"})

    # Recreate graph definition
    try:
        if db.has_graph(target_graph_name):
            if conflict_resolution == "error":
                raise ValueError(f"Graph '{target_graph_name}' already exists")
            elif conflict_resolution == "overwrite":
                db.delete_graph(target_graph_name, ignore_missing=True)

        # Create graph with original edge definitions
        # API Convention: python-arango returns snake_case keys (not camelCase)
        # Extract edge_definitions and orphan_collections from backed-up graph properties
        edge_definitions = graph_properties.get("edge_definitions", [])
        orphan_collections = graph_properties.get("orphan_collections", [])

        graph = db.create_graph(
            name=target_graph_name,
            edge_definitions=edge_definitions,
            orphan_collections=orphan_collections
        )

        graph_created = True
    except Exception as e:
        errors.append({"operation": "create_graph", "error": str(e), "type": "graph"})
        graph_created = False

    # Validate integrity if requested
    integrity_report = None
    if validate_integrity and graph_created:
        try:
            integrity_report = validate_graph_integrity(db, target_graph_name, True, True, False)
        except Exception as e:
            errors.append({"operation": "integrity_validation", "error": str(e), "type": "validation"})

    return {
        "graph_name": target_graph_name,
        "original_graph_name": original_graph_name,
        "input_dir": input_dir,
        "restored_vertices": restored_vertices,
        "restored_edges": restored_edges,
        "graph_created": graph_created,
        "conflicts": conflicts,
        "errors": errors,
        "integrity_report": integrity_report,
        "total_documents_restored": sum(r.get("inserted", 0) + r.get("updated", 0) for r in restored_vertices + restored_edges),
    }


def _restore_collection_from_file(
    db: StandardDatabase,
    collection_name: str,
    file_path: str,
    conflict_resolution: str
) -> Dict[str, Any]:
    """Helper to restore single collection from JSON file with conflict handling.

    Args:
        db: Database instance
        collection_name: Name of collection to restore
        file_path: Path to JSON backup file
        conflict_resolution: Conflict resolution strategy

    Returns:
        Dictionary with restore statistics
    """
    # Load documents
    with open(file_path, "r", encoding="utf-8") as f:
        documents = json.load(f)

    # Create collection if needed
    if not db.has_collection(collection_name):
        # Determine if edge collection based on document structure
        is_edge = any("_from" in doc and "_to" in doc for doc in documents[:5])
        db.create_collection(collection_name, edge=is_edge)

    col = db.collection(collection_name)

    # Insert with conflict resolution
    inserted = 0
    updated = 0
    skipped = 0
    errors = []

    for doc in documents:
        try:
            if conflict_resolution == "skip" and col.has(doc["_key"]):
                skipped += 1
            elif conflict_resolution == "overwrite":
                try:
                    col.replace(doc)
                    updated += 1
                except:
                    col.insert(doc)
                    inserted += 1
            else:  # error mode
                col.insert(doc)
                inserted += 1
        except Exception as e:
            if conflict_resolution == "error":
                raise
            errors.append({"document_key": doc.get("_key"), "error": str(e)})
            skipped += 1

    return {
        "collection": collection_name,
        "inserted": inserted,
        "updated": updated,
        "skipped": skipped,
        "errors": len(errors),
        "total_processed": len(documents),
    }


def validate_graph_integrity(
    db: StandardDatabase,
    graph_name: Optional[str] = None,
    check_orphaned_edges: bool = True,
    check_constraints: bool = True,
    return_details: bool = False
) -> Dict[str, Any]:
    """Validate graph consistency and constraints.

    Args:
        db: Database instance
        graph_name: Specific graph to validate (all if None)
        check_orphaned_edges: Check for edges with missing vertices
        check_constraints: Validate graph constraints
        return_details: Return detailed violation information

    Returns:
        Dictionary with validation results
    """
    if graph_name:
        graphs_to_check = [graph_name] if db.has_graph(graph_name) else []
    else:
        graphs_to_check = [g["name"] for g in db.graphs()]

    validation_results = []
    total_orphaned = 0
    total_violations = 0

    for gname in graphs_to_check:
        graph = db.graph(gname)
        graph_props = graph.properties()

        orphaned_edges = []
        constraint_violations = []

        if check_orphaned_edges:
            # Check each edge collection for orphaned edges
            # API Convention: python-arango returns snake_case keys (not camelCase)
            # Each edge_def contains: edge_collection, from_vertex_collections, to_vertex_collections
            for edge_def in graph_props.get("edge_definitions", []):
                edge_col_name = edge_def["edge_collection"]
                from_collections = edge_def.get("from_vertex_collections", [])
                to_collections = edge_def.get("to_vertex_collections", [])

                if db.has_collection(edge_col_name):
                    edge_col = db.collection(edge_col_name)

                    # Sample edges to check for orphans
                    sample_query = f"""
                    FOR edge IN {edge_col_name}
                    LET from_exists = DOCUMENT(edge._from) != null
                    LET to_exists = DOCUMENT(edge._to) != null
                    FILTER !from_exists OR !to_exists
                    RETURN {{
                        _id: edge._id,
                        _from: edge._from,
                        _to: edge._to,
                        from_exists: from_exists,
                        to_exists: to_exists
                    }}
                    """

                    try:
                        cursor = db.aql.execute(sample_query)
                        for orphan in cursor:
                            orphaned_edges.append(orphan)
                            total_orphaned += 1
                    except Exception as e:
                        constraint_violations.append({
                            "type": "query_error",
                            "collection": edge_col_name,
                            "error": str(e)
                        })

        # Accumulate total violations for this graph
        total_violations += len(constraint_violations)

        validation_results.append({
            "graph_name": gname,
            "valid": len(orphaned_edges) == 0 and len(constraint_violations) == 0,
            "orphaned_edges_count": len(orphaned_edges),
            "constraint_violations_count": len(constraint_violations),
            "orphaned_edges": orphaned_edges if return_details else [],
            "constraint_violations": constraint_violations if return_details else [],
        })

    overall_valid = total_orphaned == 0 and total_violations == 0

    return {
        "valid": overall_valid,
        "graphs_checked": len(graphs_to_check),
        "total_orphaned_edges": total_orphaned,
        "total_constraint_violations": total_violations,
        "results": validation_results,
        "summary": f"Checked {len(graphs_to_check)} graphs: {total_orphaned} orphaned edges, {total_violations} violations"
    }


def calculate_graph_statistics(
    db: StandardDatabase,
    graph_name: Optional[str] = None,
    include_degree_distribution: bool = True,
    include_connectivity: bool = True,
    sample_size: Optional[int] = None,
    aggregate_collections: bool = False,
    per_collection_stats: bool = False
) -> Dict[str, Any]:
    """Generate comprehensive graph analytics with improved representativeness.

    Args:
        db: Database instance
        graph_name: Specific graph to analyze (all if None)
        include_degree_distribution: Calculate degree distribution
        include_connectivity: Calculate connectivity metrics
        sample_size: Sample size for large graphs
        aggregate_collections: If True, aggregate stats across all collections
        per_collection_stats: If True, provide per-collection breakdown

    Returns:
        Dictionary with graph statistics
    """
    if graph_name:
        graphs_to_analyze = [graph_name] if db.has_graph(graph_name) else []
    else:
        graphs_to_analyze = [g["name"] for g in db.graphs()]

    if not graphs_to_analyze:
        return {"error": "No graphs found to analyze", "type": "NoGraphsFound"}

    statistics = []

    for gname in graphs_to_analyze:
        graph = db.graph(gname)
        graph_props = graph.properties()

        # Basic counts - extract all vertex and edge collections from graph structure
        vertex_collections = set()
        edge_collections = set()

        # API Convention: python-arango returns snake_case keys (not camelCase)
        # Graph properties structure matches the format used in backup_graph_to_dir()
        # See: https://docs.python-arango.com/en/main/specs.html#graph-management
        for edge_def in graph_props.get("edge_definitions", []):
            edge_collections.add(edge_def["edge_collection"])
            vertex_collections.update(edge_def.get("from_vertex_collections", []))
            vertex_collections.update(edge_def.get("to_vertex_collections", []))

        # Include orphan collections (vertex collections without edges)
        vertex_collections.update(graph_props.get("orphan_collections", []))

        # Count documents
        total_vertices = sum(db.collection(col).count() for col in vertex_collections if db.has_collection(col))
        total_edges = sum(db.collection(col).count() for col in edge_collections if db.has_collection(col))

        graph_stats = {
            "graph_name": gname,
            "vertex_collections": list(vertex_collections),
            "edge_collections": list(edge_collections),
            "total_vertices": total_vertices,
            "total_edges": total_edges,
            "density": total_edges / (total_vertices * (total_vertices - 1)) if total_vertices > 1 else 0,
        }

        # Degree distribution analysis
        if include_degree_distribution and edge_collections:
            try:
                if aggregate_collections and len(edge_collections) > 1:
                    # Aggregate across all edge collections
                    union_queries = []
                    for edge_col in edge_collections:
                        if db.has_collection(edge_col):
                            union_queries.append(f"FOR edge IN {edge_col} RETURN {{_from: edge._from, _to: edge._to}}")

                    if union_queries:
                        degree_query = f"""
                        LET all_edges = UNION({', '.join(f'({q})' for q in union_queries)})
                        FOR edge IN all_edges
                        COLLECT vertex = edge._from WITH COUNT INTO out_degree
                        COLLECT degree = out_degree WITH COUNT INTO frequency
                        SORT degree
                        RETURN {{degree: degree, frequency: frequency}}
                        """

                        cursor = db.aql.execute(degree_query)
                        degree_dist = list(cursor)
                        graph_stats["out_degree_distribution"] = degree_dist
                        graph_stats["degree_analysis_method"] = "aggregated_all_collections"

                        if degree_dist:
                            degrees = [d["degree"] for d in degree_dist]
                            graph_stats["max_out_degree"] = max(degrees)
                            graph_stats["avg_out_degree"] = total_edges / total_vertices if total_vertices > 0 else 0

                elif per_collection_stats:
                    # Per-collection degree distribution
                    per_collection_degrees = {}
                    for edge_col in edge_collections:
                        if db.has_collection(edge_col):
                            degree_query = f"""
                            FOR edge IN {edge_col}
                            COLLECT vertex = edge._from WITH COUNT INTO out_degree
                            COLLECT degree = out_degree WITH COUNT INTO frequency
                            SORT degree
                            RETURN {{degree: degree, frequency: frequency}}
                            """

                            cursor = db.aql.execute(degree_query)
                            per_collection_degrees[edge_col] = list(cursor)

                    graph_stats["per_collection_degree_distribution"] = per_collection_degrees
                    graph_stats["degree_analysis_method"] = "per_collection"

                else:
                    # Default: use first collection (with warning about sampling)
                    first_edge_col = list(edge_collections)[0]
                    degree_query = f"""
                    FOR edge IN {first_edge_col}
                    COLLECT vertex = edge._from WITH COUNT INTO out_degree
                    COLLECT degree = out_degree WITH COUNT INTO frequency
                    SORT degree
                    RETURN {{degree: degree, frequency: frequency}}
                    """

                    cursor = db.aql.execute(degree_query)
                    degree_dist = list(cursor)
                    graph_stats["out_degree_distribution"] = degree_dist
                    graph_stats["degree_analysis_method"] = f"sampled_from_{first_edge_col}"
                    graph_stats["degree_analysis_warning"] = f"Degree distribution calculated from {first_edge_col} only. Use aggregate_collections=True for complete analysis."

                    if degree_dist:
                        degrees = [d["degree"] for d in degree_dist]
                        graph_stats["max_out_degree"] = max(degrees)
                        graph_stats["avg_out_degree"] = total_edges / total_vertices if total_vertices > 0 else 0

            except Exception as e:
                graph_stats["degree_distribution_error"] = str(e)

        # Connectivity analysis
        if include_connectivity and total_vertices > 0:
            try:
                sample_limit = min(sample_size or 100, total_vertices)

                if per_collection_stats and len(vertex_collections) > 1:
                    # Per-collection connectivity analysis
                    per_collection_connectivity = {}
                    for vertex_col in vertex_collections:
                        if db.has_collection(vertex_col):
                            col_sample_limit = min(sample_limit // len(vertex_collections), db.collection(vertex_col).count())
                            if col_sample_limit > 0:
                                connectivity_query = f"""
                                FOR v IN {vertex_col}
                                LIMIT {col_sample_limit}
                                LET reachable = LENGTH(
                                    FOR vertex, edge, path IN 1..10 OUTBOUND v._id
                                    GRAPH '{gname}'
                                    RETURN vertex
                                )
                                RETURN {{vertex: v._id, reachable_count: reachable}}
                                """

                                cursor = db.aql.execute(connectivity_query)
                                connectivity_data = list(cursor)

                                if connectivity_data:
                                    reachable_counts = [c["reachable_count"] for c in connectivity_data]
                                    per_collection_connectivity[vertex_col] = {
                                        "sample_size": len(connectivity_data),
                                        "avg_reachable": sum(reachable_counts) / len(reachable_counts),
                                        "max_reachable": max(reachable_counts),
                                        "min_reachable": min(reachable_counts)
                                    }

                    graph_stats["per_collection_connectivity"] = per_collection_connectivity
                    graph_stats["connectivity_analysis_method"] = "per_collection"

                elif aggregate_collections and len(vertex_collections) > 1:
                    # Sample across all vertex collections proportionally
                    total_sample_data = []
                    for vertex_col in vertex_collections:
                        if db.has_collection(vertex_col):
                            col_count = db.collection(vertex_col).count()
                            col_sample_limit = max(1, int((col_count / total_vertices) * sample_limit))

                            connectivity_query = f"""
                            FOR v IN {vertex_col}
                            LIMIT {col_sample_limit}
                            LET reachable = LENGTH(
                                FOR vertex, edge, path IN 1..10 OUTBOUND v._id
                                GRAPH '{gname}'
                                RETURN vertex
                            )
                            RETURN {{vertex: v._id, reachable_count: reachable, collection: '{vertex_col}'}}
                            """

                            cursor = db.aql.execute(connectivity_query)
                            total_sample_data.extend(list(cursor))

                    if total_sample_data:
                        reachable_counts = [c["reachable_count"] for c in total_sample_data]
                        graph_stats["connectivity_sample_size"] = len(total_sample_data)
                        graph_stats["avg_reachable_vertices"] = sum(reachable_counts) / len(reachable_counts)
                        graph_stats["max_reachable_vertices"] = max(reachable_counts)
                        graph_stats["min_reachable_vertices"] = min(reachable_counts)
                        graph_stats["connectivity_analysis_method"] = "aggregated_proportional_sampling"

                        # Collection breakdown
                        collection_breakdown = {}
                        for item in total_sample_data:
                            col = item["collection"]
                            if col not in collection_breakdown:
                                collection_breakdown[col] = []
                            collection_breakdown[col].append(item["reachable_count"])

                        graph_stats["connectivity_collection_breakdown"] = {
                            col: {"sample_size": len(counts), "avg_reachable": sum(counts) / len(counts)}
                            for col, counts in collection_breakdown.items()
                        }

                else:
                    # Default: sample from first collection (with warning)
                    first_vertex_col = list(vertex_collections)[0]
                    connectivity_query = f"""
                    FOR v IN {first_vertex_col}
                    LIMIT {sample_limit}
                    LET reachable = LENGTH(
                        FOR vertex, edge, path IN 1..10 OUTBOUND v._id
                        GRAPH '{gname}'
                        RETURN vertex
                    )
                    RETURN {{vertex: v._id, reachable_count: reachable}}
                    """

                    cursor = db.aql.execute(connectivity_query)
                    connectivity_data = list(cursor)

                    if connectivity_data:
                        reachable_counts = [c["reachable_count"] for c in connectivity_data]
                        graph_stats["connectivity_sample_size"] = len(connectivity_data)
                        graph_stats["avg_reachable_vertices"] = sum(reachable_counts) / len(reachable_counts)
                        graph_stats["max_reachable_vertices"] = max(reachable_counts)
                        graph_stats["connectivity_analysis_method"] = f"sampled_from_{first_vertex_col}"
                        graph_stats["connectivity_analysis_warning"] = f"Connectivity sampled from {first_vertex_col} only. Use aggregate_collections=True for complete analysis."

            except Exception as e:
                graph_stats["connectivity_analysis_error"] = str(e)

        statistics.append(graph_stats)

    return {
        "graphs_analyzed": len(statistics),
        "statistics": statistics,
        "analysis_timestamp": datetime.now().isoformat(),
    }
