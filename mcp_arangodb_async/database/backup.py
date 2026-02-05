"""Database backup and restore operations."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from arango.database import StandardDatabase

logger = logging.getLogger(__name__)

BATCH_SIZE = 1000


def backup_database(
    db: StandardDatabase,
    args: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Backup entire database or specific collections.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing:
            - output_dir (optional): Output directory (default: backups/timestamp)
            - collections (optional): List of collection names (default: all)
            - type (optional): "collection" | "graph" | "view" | "all" (default: "all")

    Returns:
        Dictionary with backup results and metadata
    """
    output_dir = args.get("output_dir")
    collections = args.get("collections")
    backup_type = args.get("type", "all")

    # Generate output directory
    if not output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"backups/{timestamp}"

    os.makedirs(output_dir, exist_ok=True)

    results = {
        "output_dir": output_dir,
        "type": backup_type,
        "collections": [],
        "graphs": [],
        "views": [],
    }

    # Backup collections
    if backup_type in ("collection", "all"):
        results["collections"] = _backup_collections(db, output_dir, collections)

    # Backup graphs
    if backup_type in ("graph", "all"):
        results["graphs"] = _backup_graphs(db, output_dir)

    # Backup views
    if backup_type in ("view", "all"):
        results["views"] = _backup_views(db, output_dir)

    # Generate metadata
    metadata = {
        "version": "4.0",
        "timestamp": datetime.now().isoformat(),
        "database": db.name,
        "type": backup_type,
        "collections": [r["name"] for r in results["collections"] if r.get("success")],
        "graphs": [r["name"] for r in results["graphs"] if r.get("success")],
        "views": [r["name"] for r in results["views"] if r.get("success")],
    }

    with open(os.path.join(output_dir, "_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    results["metadata"] = metadata
    return results


def restore_database(
    db: StandardDatabase,
    args: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Restore database from backup directory.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing:
            - input_dir (required): Backup directory path
            - collections (optional): List of collection names to restore
            - type (optional): "collection" | "graph" | "view" | "all"
            - conflict (optional): "skip" | "replace" | "update" (default: "skip")

    Returns:
        Dictionary with restore results
    """
    input_dir = args.get("input_dir")
    if not input_dir:
        return {"error": "input_dir is required"}

    if not os.path.exists(input_dir):
        return {"error": f"Backup directory not found: {input_dir}"}

    collections = args.get("collections")
    restore_type = args.get("type", "all")
    conflict = args.get("conflict", "skip")

    # Load metadata
    metadata_file = os.path.join(input_dir, "_metadata.json")
    if os.path.exists(metadata_file):
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    else:
        metadata = None

    results = {
        "input_dir": input_dir,
        "type": restore_type,
        "collections": [],
        "graphs": [],
        "views": [],
        "metadata": metadata,
    }

    # Restore collections
    if restore_type in ("collection", "all"):
        results["collections"] = _restore_collections(
            db, input_dir, collections, conflict
        )

    # Restore graphs
    if restore_type in ("graph", "all"):
        results["graphs"] = _restore_graphs(db, input_dir)

    # Restore views
    if restore_type in ("view", "all"):
        results["views"] = _restore_views(db, input_dir)

    return results


def _backup_collections(
    db: StandardDatabase,
    output_dir: str,
    collections: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Backup collections."""
    if not collections:
        collections = [
            c["name"] for c in db.collections()
            if not c["name"].startswith("_")
        ]

    results = []
    for name in collections:
        if not db.has_collection(name):
            results.append({"name": name, "success": False, "error": "Not found"})
            continue

        try:
            col = db.collection(name)
            props = col.properties()
            is_edge = props.get("type") == 3

            # Backup documents
            docs = list(db.aql.execute(f"FOR d IN {name} RETURN d"))
            with open(os.path.join(output_dir, f"{name}.json"), "w", encoding="utf-8") as f:
                json.dump(docs, f, indent=2, default=str, ensure_ascii=False)

            # Backup metadata
            indexes = [idx for idx in col.indexes() if idx["type"] != "primary"]
            meta = {
                "name": name,
                "type": "edge" if is_edge else "document",
                "indexes": indexes
            }
            with open(os.path.join(output_dir, f"{name}.meta.json"), "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)

            results.append({
                "name": name,
                "type": meta["type"],
                "count": len(docs),
                "indexes": len(indexes),
                "success": True
            })

        except Exception as e:
            logger.exception(f"Failed to backup {name}: {e}")
            results.append({"name": name, "success": False, "error": str(e)})

    return results


def _backup_graphs(db: StandardDatabase, output_dir: str) -> List[Dict[str, Any]]:
    """Backup graphs."""
    results = []
    try:
        graphs = db.graphs()
        for graph_info in graphs:
            name = graph_info["name"]
            if name.startswith("_"):
                continue

            graph = db.graph(name)
            graph_def = {
                "name": name,
                "edgeDefinitions": graph_info.get("edgeDefinitions", []),
                "orphanCollections": graph_info.get("orphanCollections", []),
            }

            with open(os.path.join(output_dir, f"graph_{name}.json"), "w", encoding="utf-8") as f:
                json.dump(graph_def, f, indent=2, ensure_ascii=False)

            results.append({"name": name, "success": True})

    except Exception as e:
        logger.exception(f"Failed to backup graphs: {e}")

    return results


def _backup_views(db: StandardDatabase, output_dir: str) -> List[Dict[str, Any]]:
    """Backup views."""
    results = []
    try:
        views = db.views()
        for view_info in views:
            name = view_info["name"]
            if name.startswith("_"):
                continue

            view = db.view(name)
            view_def = view.properties()

            with open(os.path.join(output_dir, f"view_{name}.json"), "w", encoding="utf-8") as f:
                json.dump(view_def, f, indent=2, ensure_ascii=False)

            results.append({"name": name, "success": True})

    except Exception as e:
        logger.exception(f"Failed to backup views: {e}")

    return results


def _restore_collections(
    db: StandardDatabase,
    input_dir: str,
    collections: Optional[List[str]] = None,
    conflict: str = "skip"
) -> List[Dict[str, Any]]:
    """Restore collections."""
    results = []

    # Find all collection backup files
    for filename in os.listdir(input_dir):
        if not filename.endswith(".json") or filename.startswith("_") or filename.startswith("graph_") or filename.startswith("view_"):
            continue

        name = filename.replace(".json", "")
        if collections and name not in collections:
            continue

        try:
            # Load metadata
            meta_file = os.path.join(input_dir, f"{name}.meta.json")
            if os.path.exists(meta_file):
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            else:
                meta = {"name": name, "type": "document"}

            # Create collection if not exists
            if not db.has_collection(name):
                db.create_collection(name, edge=(meta.get("type") == "edge"))

            # Load documents
            with open(os.path.join(input_dir, filename), "r", encoding="utf-8") as f:
                docs = json.load(f)

            # Insert documents
            col = db.collection(name)
            imported = 0
            for doc in docs:
                try:
                    if conflict == "replace":
                        col.insert(doc, overwrite=True)
                    elif conflict == "update":
                        col.update(doc, merge=True)
                    else:  # skip
                        col.insert(doc, silent=True)
                    imported += 1
                except:
                    pass

            results.append({
                "name": name,
                "type": meta.get("type"),
                "total": len(docs),
                "imported": imported,
                "success": True
            })

        except Exception as e:
            logger.exception(f"Failed to restore {name}: {e}")
            results.append({"name": name, "success": False, "error": str(e)})

    return results


def _restore_graphs(db: StandardDatabase, input_dir: str) -> List[Dict[str, Any]]:
    """Restore graphs."""
    results = []

    for filename in os.listdir(input_dir):
        if not filename.startswith("graph_") or not filename.endswith(".json"):
            continue

        try:
            with open(os.path.join(input_dir, filename), "r", encoding="utf-8") as f:
                graph_def = json.load(f)

            name = graph_def["name"]
            if not db.has_graph(name):
                db.create_graph(
                    name,
                    edge_definitions=graph_def.get("edgeDefinitions", []),
                    orphan_collections=graph_def.get("orphanCollections", [])
                )

            results.append({"name": name, "success": True})

        except Exception as e:
            logger.exception(f"Failed to restore graph: {e}")
            results.append({"name": filename, "success": False, "error": str(e)})

    return results


def _restore_views(db: StandardDatabase, input_dir: str) -> List[Dict[str, Any]]:
    """Restore views."""
    results = []

    for filename in os.listdir(input_dir):
        if not filename.startswith("view_") or not filename.endswith(".json"):
            continue

        try:
            with open(os.path.join(input_dir, filename), "r", encoding="utf-8") as f:
                view_def = json.load(f)

            name = view_def.get("name")
            if name and not db.has_view(name):
                db.create_view(name, "arangosearch", view_def)

            results.append({"name": name, "success": True})

        except Exception as e:
            logger.exception(f"Failed to restore view: {e}")
            results.append({"name": filename, "success": False, "error": str(e)})

    return results
