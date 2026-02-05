"""
Arango CLI - Unified CLI interface for V4 tools

Provides direct access to all V4 tool operations:
- arango_database: list, get_focused, switch, get_resolution
- arango_collection: insert, find, update, remove, bulk operations, indexes, schema
- arango_view: create, manage, search views
- arango_graph: create, traverse, backup/restore
- arango_aql: query, explain, profile, build
- arango_mcp: search_tools, workflows, usage_stats

Usage:
    maa arango <tool> <action> [options]

Examples:
    maa arango database list
    maa arango collection insert notes --data '{"title": "Hello"}'
    maa arango aql query "FOR doc IN notes RETURN doc"
    maa arango graph traverse myGraph --start vertices/1 --direction outbound
"""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict

from ..utility.config import load_config
from ..utility.db import get_client_and_db

# V4 tool handlers
from ..database.handler import handle_database
from ..collection.handler import handle_collection
from ..view.handler import handle_view
from ..graph.handler import handle_graph
from ..aql.handler import handle_aql
from ..mcp.handler import handle_mcp
from ..template.handler import handle_template

logger = logging.getLogger(__name__)

# Tool registry
TOOLS = {
    "database": {
        "handler": handle_database,
        "operations": ["list", "get_focused", "switch", "get_resolution", "backup", "restore"],
    },
    "collection": {
        "handler": handle_collection,
        "operations": [
            "insert", "find", "update", "remove", "insert_with_validation", "list",
            "bulk_insert", "bulk_update", "import", "export",
            "list_indexes", "create_index", "delete_index",
            "get_schema", "create_schema", "validate_document", "validate_references",
            "create", "stats", "drop", "truncate",
            "backup",
        ],
    },
    "view": {
        "handler": handle_view,
        "operations": ["create", "drop", "list", "get", "update", "search"],
    },
    "graph": {
        "handler": handle_graph,
        "operations": [
            "create", "list", "add_vertex_collection", "add_edge_definition",
            "add_edge", "traverse", "shortest_path",
            "backup", "restore", "backup_named",
            "validate_integrity", "statistics",
        ],
    },
    "aql": {
        "handler": handle_aql,
        "operations": ["query", "explain", "profile", "build"],
    },
    "mcp": {
        "handler": handle_mcp,
        "operations": ["search_tools", "list_by_category", "get_workflow", "list_workflows", "usage_stats", "unload"],
    },
    "template": {
        "handler": handle_template,
        "operations": ["execute"],
    },
}


def handle_arango_command(args) -> int:
    """Execute arango CLI command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code: 0 for success, 1 for error
    """
    tool = args.arango_tool
    action = args.arango_action

    # Validate tool
    if tool not in TOOLS:
        print(f"Error: Unknown tool '{tool}'", file=sys.stderr)
        print(f"Available tools: {', '.join(TOOLS.keys())}", file=sys.stderr)
        return 1

    # Validate action
    tool_info = TOOLS[tool]
    if action not in tool_info["operations"]:
        print(f"Error: Unknown action '{action}' for tool '{tool}'", file=sys.stderr)
        print(f"Available actions: {', '.join(tool_info['operations'])}", file=sys.stderr)
        return 1

    # Load config and connect to database
    try:
        cfg = load_config()
        client, db = get_client_and_db(cfg)
    except Exception as e:
        print(f"Error: Failed to connect to database: {e}", file=sys.stderr)
        return 1

    # Build arguments from CLI options
    tool_args: Dict[str, Any] = {}

    # Common parameters
    if hasattr(args, "collection") and args.collection:
        tool_args["collection"] = args.collection
    if hasattr(args, "data") and args.data:
        try:
            tool_args["data"] = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --data: {e}", file=sys.stderr)
            return 1
    if hasattr(args, "filter") and args.filter:
        try:
            tool_args["filter"] = json.loads(args.filter)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --filter: {e}", file=sys.stderr)
            return 1
    if hasattr(args, "key") and args.key:
        tool_args["key"] = args.key
    if hasattr(args, "query") and args.query:
        tool_args["query"] = args.query
    if hasattr(args, "limit") and args.limit:
        tool_args["limit"] = args.limit

    # Template-specific parameters
    if hasattr(args, "name") and args.name:
        tool_args["name"] = args.name
    if hasattr(args, "params") and args.params:
        try:
            tool_args["params"] = json.loads(args.params)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --params: {e}", file=sys.stderr)
            return 1

    # Backup/restore parameters
    if hasattr(args, "output_dir") and args.output_dir:
        tool_args["output_dir"] = args.output_dir
    if hasattr(args, "input_dir") and args.input_dir:
        tool_args["input_dir"] = args.input_dir
    if hasattr(args, "collections") and args.collections:
        # Convert comma-separated string to list
        tool_args["collections"] = [c.strip() for c in args.collections.split(",")]
    if hasattr(args, "type") and args.type:
        tool_args["type"] = args.type
    if hasattr(args, "conflict") and args.conflict:
        tool_args["conflict"] = args.conflict

    # Execute tool operation
    try:
        handler = tool_info["handler"]
        # Template handler has different signature (no action parameter)
        if tool == "template":
            result = handler(db, tool_args if tool_args else {})
        else:
            result = handler(db, action, tool_args if tool_args else None)

        # Output result as JSON
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Check for errors
        if isinstance(result, dict) and "error" in result:
            return 1

        return 0

    except Exception as e:
        print(f"Error: Operation failed: {e}", file=sys.stderr)
        logger.exception("Arango CLI operation failed")
        return 1
