"""Collection backup operations."""

from typing import Any, Dict
from arango.database import StandardDatabase


def backup(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
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

    # Import here to avoid circular imports during module initialization
    from mcp_arangodb_async.backup import backup_collections_to_dir

    report = backup_collections_to_dir(
        db, output_dir=output_dir, collections=collections, doc_limit=doc_limit
    )
    return report
