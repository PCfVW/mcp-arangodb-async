"""
Output Size Control Utility

Controls MCP output length to avoid token limits.
Mechanism: Calculate JSON length → truncate if exceeds limit + warning

Environment Variables:
    MCP_MAX_OUTPUT_K: Maximum output size in K (default 8, i.e., 8192 chars)
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

# Read K size from environment, default 8K
_size_k = int(os.getenv("MCP_MAX_OUTPUT_K", "8"))
MAX_OUTPUT_SIZE = _size_k * 1024

TRUNCATE_WARNING = (
    f"\n\n⚠️ Output truncated (exceeds {_size_k}K), data incomplete. "
    "Suggestions: use LIMIT to reduce results, add FILTER conditions, or specify RETURN fields."
)


def format_output(data: Dict[str, Any], max_size: int = MAX_OUTPUT_SIZE) -> Dict[str, Any]:
    """
    Format output and control size.

    Args:
        data: Data to output
        max_size: Maximum output size (default 8192)

    Returns:
        If < max_size: return as-is
        If > max_size: truncate JSON + add warning
    """
    try:
        json_str = json.dumps(data, ensure_ascii=False, indent=None, default=str)
    except (TypeError, ValueError):
        json_str = str(data)

    # Check size
    if len(json_str) <= max_size:
        return data

    # Truncate
    logger = __import__("logging").getLogger(__name__)
    logger.warning(f"Output size {len(json_str)} exceeds limit {max_size}, truncating")

    # Try to truncate intelligently
    truncated = _truncate_data(data, max_size)
    return truncated


def _truncate_data(data: Dict[str, Any], max_size: int) -> Dict[str, Any]:
    """
    Intelligently truncate data structure.

    Strategy:
    1. If 'results'/'items'/'data' list exists, truncate it
    2. Add truncation warning
    3. Preserve metadata (count, etc.)
    """
    result = data.copy()

    # Find truncatable list field
    list_keys = ["results", "items", "data", "rows", "documents"]
    truncated_key = None

    for key in list_keys:
        if key in result and isinstance(result[key], list) and len(result[key]) > 0:
            truncated_key = key
            break

    if truncated_key:
        # Truncate list until size fits
        original_list = result[truncated_key]
        truncated_list = []
        current_size = 0

        for item in original_list:
            item_str = json.dumps(item, ensure_ascii=False, default=str)
            if current_size + len(item_str) < max_size * 0.8:  # Leave room for metadata
                truncated_list.append(item)
                current_size += len(item_str)
            else:
                break

        result[truncated_key] = truncated_list
        result["_truncated"] = True
        result["_original_count"] = len(original_list)
        result["_returned_count"] = len(truncated_list)
        result["_warning"] = TRUNCATE_WARNING.strip()

    else:
        # No list to truncate, just add warning
        result["_truncated"] = True
        result["_warning"] = TRUNCATE_WARNING.strip()

    return result


def format_find_compact(results: List[Dict[str, Any]], max_size: int = MAX_OUTPUT_SIZE) -> Dict[str, Any]:
    """
    Format find results in compact mode.

    Returns only essential fields:
    - _key, _id
    - title (if exists)
    - tags (if exists)
    - weight (if exists)

    Args:
        results: Query results
        max_size: Maximum output size

    Returns:
        Formatted compact results
    """
    compact = []
    for item in results:
        if not isinstance(item, dict):
            continue

        compact_item = {}

        # Essential fields
        if "_key" in item:
            compact_item["_key"] = item["_key"]
        if "_id" in item:
            compact_item["_id"] = item["_id"]

        # Optional important fields
        if "title" in item:
            compact_item["title"] = item["title"]
        if "tags" in item:
            compact_item["tags"] = item["tags"]
        if "weight" in item:
            compact_item["weight"] = item["weight"]

        compact.append(compact_item)

    data = {
        "count": len(compact),
        "results": compact
    }

    return format_output(data, max_size)
