"""
ArangoDB MCP Server - Backup Utilities

This module provides functionality to backup ArangoDB collections to JSON files.
Supports exporting single or multiple collections with optional document limits.

Functions:
- validate_output_directory() - Validate/sanitize output directory for backups
- backup_collections_to_dir() - Export collections to JSON files in a directory
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from arango.database import StandardDatabase


def validate_output_directory(output_dir: str) -> str:
    """Validate and sanitize output directory to prevent path traversal attacks.

    Args:
        output_dir: The requested output directory path

    Returns:
        Validated and normalized absolute path

    Raises:
        ValueError: If the path is invalid or contains path traversal attempts
    """
    # Convert to absolute path and resolve any .. components
    abs_path = os.path.abspath(output_dir)

    # Check for obvious path traversal attempts in the original path
    if '..' in output_dir:
        raise ValueError("Path traversal detected: '..' not allowed in path")

    # For security, ensure the path doesn't contain suspicious patterns
    suspicious_patterns = ['../', '..\\', '/../', '\\..\\']
    for pattern in suspicious_patterns:
        if pattern in output_dir:
            raise ValueError(f"Suspicious path pattern detected: {pattern}")

    # Allow temporary directories for testing (they typically start with /tmp or contain 'temp')
    import tempfile
    temp_dir = tempfile.gettempdir()
    if abs_path.startswith(temp_dir):
        return abs_path

    # For production use, ensure path is within current working directory
    cwd = os.getcwd()
    try:
        # This will raise ValueError if abs_path is not relative to cwd
        rel_path = os.path.relpath(abs_path, cwd)
        # Ensure the relative path doesn't start with .. (going up from cwd)
        if rel_path.startswith('..'):
            raise ValueError("Path outside current working directory")
    except ValueError as e:
        # Allow if it's a cross-drive issue on Windows but still within reasonable bounds
        if os.name == 'nt' and 'different drives' in str(e).lower():
            # On Windows, allow if it's a temp directory or reasonable absolute path
            if 'temp' in abs_path.lower() or abs_path.startswith(temp_dir):
                return abs_path
        raise ValueError(f"Output directory '{output_dir}' is not allowed. Must be within current working directory or temp directory.")

    return abs_path


def backup_collections_to_dir(
    db: StandardDatabase,
    output_dir: Optional[str] = None,
    collections: Optional[List[str]] = None,
    doc_limit: Optional[int] = None,
) -> Dict[str, object]:
    """
    Dump selected (or all non-system) collections to JSON files in output_dir.

    Each collection is written as a JSON array of documents: <name>.json
    Returns a report dict with written file paths and record counts.
    """
    # Determine target directory
    if output_dir is None or not output_dir.strip():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("backups", ts)

    # Validate and sanitize the output directory
    try:
        output_dir = validate_output_directory(output_dir)
    except ValueError as e:
        raise ValueError(f"Invalid output directory: {e}")

    os.makedirs(output_dir, exist_ok=True)

    # Resolve which collections to export
    all_cols = [c["name"] for c in db.collections() if not c.get("isSystem")]
    target_cols = collections if collections else all_cols

    written: List[Dict[str, object]] = []

    for name in target_cols:
        if name not in all_cols:
            # Skip unknown/non-existing or system collections silently
            continue

        col = db.collection(name)
        path = os.path.join(output_dir, f"{name}.json")

        # Use streaming approach to handle large collections
        try:
            cursor = col.all()
            count = 0

            with open(path, "w", encoding="utf-8") as f:
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

            written.append({"collection": name, "path": path, "count": count})

        except Exception as e:
            # Log error but continue with other collections
            written.append({
                "collection": name,
                "path": path,
                "count": 0,
                "error": str(e)
            })
        finally:
            # Ensure cursor is closed if it exists
            if 'cursor' in locals() and hasattr(cursor, 'close'):
                try:
                    cursor.close()
                except Exception:
                    pass  # Ignore cleanup errors

    return {
        "output_dir": output_dir,
        "written": written,
        "total_collections": len(written),
        "total_documents": sum(int(x["count"]) for x in written),
    }
