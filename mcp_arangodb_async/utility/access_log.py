"""Access log utilities.

Records access and admin execution events for:
- lightweight access tracking
- behavior/relationship analysis inputs
- job-level observability for admin pipelines
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from arango.database import StandardDatabase

logger = logging.getLogger(__name__)

ACCESS_LOGS_COLLECTION = "access_logs"

# Access types
ACCESS_TYPE_QUERY = 1
ACCESS_TYPE_UPDATE = 2
ACCESS_TYPE_TEMPLATE = 3
ACCESS_TYPE_ADMIN = 4

# Collections considered edge-like for log classification
EDGE_COLLECTIONS = {"edges", "tag_edges", "rules_edges", "skills_edges"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _collection_from_id(doc_id: str) -> str:
    if not isinstance(doc_id, str) or "/" not in doc_id:
        return ""
    return doc_id.split("/", 1)[0]


def _is_edge_id(doc_id: str) -> bool:
    col = _collection_from_id(doc_id)
    return col in EDGE_COLLECTIONS or col.endswith("_edges")


def _should_skip_target(target_ref: str) -> bool:
    # Prevent recursive self-logging noise.
    if target_ref.startswith("access_logs/"):
        return True
    return False


def ensure_access_logs_collection(db: StandardDatabase) -> None:
    """Ensure access_logs collection and basic indexes exist."""
    if db.has_collection(ACCESS_LOGS_COLLECTION):
        return

    db.create_collection(ACCESS_LOGS_COLLECTION)
    logger.info("Created collection: %s", ACCESS_LOGS_COLLECTION)

    col = db.collection(ACCESS_LOGS_COLLECTION)
    col.add_hash_index(fields=["target_ref"], unique=False)
    col.add_skiplist_index(fields=["timestamp"], unique=False)
    col.add_hash_index(fields=["access_type"], unique=False)
    col.add_hash_index(fields=["target_type"], unique=False)
    logger.info("Created indexes for %s", ACCESS_LOGS_COLLECTION)


def log_access(
    db: StandardDatabase,
    targets: List[str],
    access_type: int = ACCESS_TYPE_QUERY,
    target_type: str = "node",
    *,
    session_id: Optional[str] = None,
    action: Optional[str] = None,
    query: Optional[str] = None,
    tags: Optional[List[str]] = None,
    related_refs: Optional[List[str]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> int:
    """Log target access records with optional behavior context."""
    if not targets:
        return 0

    # De-duplicate and filter noisy self references.
    filtered_targets = [t for t in dict.fromkeys(targets) if isinstance(t, str) and t and not _should_skip_target(t)]
    if not filtered_targets:
        return 0

    try:
        ensure_access_logs_collection(db)
        col = db.collection(ACCESS_LOGS_COLLECTION)

        timestamp = _now_iso()
        docs: List[Dict[str, Any]] = []
        for target in filtered_targets:
            doc: Dict[str, Any] = {
                "target_ref": target,
                "target_type": target_type,
                "access_type": access_type,
                "timestamp": timestamp,
            }
            if session_id:
                doc["session_id"] = session_id
            if action:
                doc["action"] = action
            if query:
                doc["query"] = query
            if tags:
                doc["tags"] = tags
            if related_refs:
                doc["related_refs"] = related_refs
            if extra:
                doc["extra"] = extra
            docs.append(doc)

        col.insert_many(docs)
        return len(docs)
    except Exception as exc:
        logger.warning("Failed to log access: %s", exc)
        return 0


def extract_ids_from_results(results: List[Any]) -> List[str]:
    """Extract document ids from common result shapes."""
    ids: List[str] = []
    for item in results:
        if not isinstance(item, dict):
            continue

        if isinstance(item.get("_id"), str):
            ids.append(item["_id"])
            continue

        # Common wrapped shapes
        for field in ("vertex", "node", "doc", "document"):
            wrapped = item.get(field)
            if isinstance(wrapped, dict) and isinstance(wrapped.get("_id"), str):
                ids.append(wrapped["_id"])

    # de-dup + skip recursion
    return [i for i in dict.fromkeys(ids) if not _should_skip_target(i)]


def log_query_results(
    db: StandardDatabase,
    results: List[Any],
    access_type: int = ACCESS_TYPE_QUERY,
    **context: Any,
) -> int:
    """Auto-log ids discovered in query results."""
    ids = extract_ids_from_results(results)
    if not ids:
        return 0

    nodes = [doc_id for doc_id in ids if not _is_edge_id(doc_id)]
    edges = [doc_id for doc_id in ids if _is_edge_id(doc_id)]

    count = 0
    if nodes:
        count += log_access(db, nodes, access_type, "node", **context)
    if edges:
        count += log_access(db, edges, access_type, "edge", **context)
    return count


def log_admin_run(
    db: StandardDatabase,
    *,
    action: str,
    dry_run: bool,
    status: str,
    metrics: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    args: Optional[Dict[str, Any]] = None,
) -> int:
    """Log one admin pipeline execution record."""
    run_id = str(uuid.uuid4())
    target_ref = f"admin_runs/{run_id}"

    extra: Dict[str, Any] = {
        "run_id": run_id,
        "status": status,
        "dry_run": dry_run,
    }
    if metrics:
        extra["metrics"] = metrics
    if args:
        extra["args"] = args

    return log_access(
        db,
        targets=[target_ref],
        access_type=ACCESS_TYPE_ADMIN,
        target_type="job",
        session_id=session_id,
        action=action,
        extra=extra,
    )
