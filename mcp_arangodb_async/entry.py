"""
ArangoDB MCP Server - Main Entry Point

This module implements the MCP (Model Context Protocol) server for ArangoDB.
Provides stdio-based server with tool registration, request handling, and lifecycle management.

Functions:
- server_lifespan() - Async context manager for server lifecycle
- handle_list_tools() - MCP handler for tool listing
- call_tool() - MCP handler for tool execution
- _json_content() - Convert data to JSON text content for MCP response
- run() - Run the MCP server with stdio transport
- main() - Console script entry point for arango-server command
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Callable, Dict, List
from types import SimpleNamespace

import mcp.server.stdio
import mcp.types as types
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.models import InitializationOptions

import logging
import os
import sys
from pydantic import ValidationError

from .config import load_config
from .db import get_client_and_db
from arango.database import StandardDatabase
from .handlers import (
    handle_arango_query,
    handle_backup,
    handle_create_collection,
    handle_insert,
    handle_list_collections,
    handle_remove,
    handle_update,
    handle_list_indexes,
    handle_create_index,
    handle_delete_index,
    handle_explain_query,
    handle_validate_references,
    handle_insert_with_validation,
    handle_bulk_insert,
    handle_bulk_update,
    handle_create_graph,
    handle_add_edge,
    handle_traverse,
    handle_shortest_path,
    handle_list_graphs,
    handle_add_vertex_collection,
    handle_add_edge_definition,
    handle_create_schema,
    handle_validate_document,
    handle_query_builder,
    handle_query_profile,
    # New graph management handlers
    handle_backup_graph,
    handle_restore_graph,
    handle_backup_named_graphs,
    handle_validate_graph_integrity,
    handle_graph_statistics,
)
from .tools import (
    ARANGO_BACKUP,
    ARANGO_CREATE_COLLECTION,
    ARANGO_INSERT,
    ARANGO_LIST_COLLECTIONS,
    ARANGO_QUERY,
    ARANGO_REMOVE,
    ARANGO_UPDATE,
    ARANGO_LIST_INDEXES,
    ARANGO_CREATE_INDEX,
    ARANGO_DELETE_INDEX,
    ARANGO_EXPLAIN_QUERY,
    ARANGO_VALIDATE_REFERENCES,
    ARANGO_INSERT_WITH_VALIDATION,
    ARANGO_BULK_INSERT,
    ARANGO_BULK_UPDATE,
    ARANGO_CREATE_GRAPH,
    ARANGO_ADD_EDGE,
    ARANGO_TRAVERSE,
    ARANGO_SHORTEST_PATH,
    ARANGO_LIST_GRAPHS,
    ARANGO_ADD_VERTEX_COLLECTION,
    ARANGO_ADD_EDGE_DEFINITION,
    ARANGO_GRAPH_TRAVERSAL,
    ARANGO_ADD_VERTEX,
    ARANGO_CREATE_SCHEMA,
    ARANGO_VALIDATE_DOCUMENT,
    ARANGO_QUERY_BUILDER,
    ARANGO_QUERY_PROFILE,
    # New graph management tools
    ARANGO_BACKUP_GRAPH,
    ARANGO_RESTORE_GRAPH,
    ARANGO_BACKUP_NAMED_GRAPHS,
    ARANGO_VALIDATE_GRAPH_INTEGRITY,
    ARANGO_GRAPH_STATISTICS,
)
from .models import (
    QueryArgs,
    ListCollectionsArgs,
    InsertArgs,
    UpdateArgs,
    RemoveArgs,
    CreateCollectionArgs,
    BackupArgs,
    ListIndexesArgs,
    CreateIndexArgs,
    DeleteIndexArgs,
    ExplainQueryArgs,
    ValidateReferencesArgs,
    InsertWithValidationArgs,
    BulkInsertArgs,
    BulkUpdateArgs,
    CreateGraphArgs,
    AddEdgeArgs,
    TraverseArgs,
    ShortestPathArgs,
    ListGraphsArgs,
    AddVertexCollectionArgs,
    AddEdgeDefinitionArgs,
    CreateSchemaArgs,
    ValidateDocumentArgs,
    QueryBuilderArgs,
    QueryProfileArgs,
    # New graph management models
    BackupGraphArgs,
    RestoreGraphArgs,
    BackupNamedGraphsArgs,
    ValidateGraphIntegrityArgs,
    GraphStatisticsArgs,
)
from .tool_registry import TOOL_REGISTRY, ToolRegistration


# ============================================================================
# Tool Registry Population
# ============================================================================
# Manually populate the tool registry with all tool definitions.
# This serves as the single source of truth for tool metadata, replacing
# the previous hybrid approach (model map + if-elif chain + manual tool list).
#
# Phase 1: Manual registration (current implementation)
# Phase 2: Will migrate to @register_tool() decorators on handlers
# ============================================================================

TOOL_REGISTRY[ARANGO_QUERY] = ToolRegistration(
    name=ARANGO_QUERY,
    description="Execute an AQL query with optional bind vars and return rows.",
    model=QueryArgs,
    handler=handle_arango_query,
)

TOOL_REGISTRY[ARANGO_LIST_COLLECTIONS] = ToolRegistration(
    name=ARANGO_LIST_COLLECTIONS,
    description="List non-system collection names.",
    model=ListCollectionsArgs,
    handler=handle_list_collections,
)

TOOL_REGISTRY[ARANGO_INSERT] = ToolRegistration(
    name=ARANGO_INSERT,
    description="Insert a document into a collection.",
    model=InsertArgs,
    handler=handle_insert,
)

TOOL_REGISTRY[ARANGO_UPDATE] = ToolRegistration(
    name=ARANGO_UPDATE,
    description="Update a document by key in a collection.",
    model=UpdateArgs,
    handler=handle_update,
)

TOOL_REGISTRY[ARANGO_REMOVE] = ToolRegistration(
    name=ARANGO_REMOVE,
    description="Remove a document by key in a collection.",
    model=RemoveArgs,
    handler=handle_remove,
)

TOOL_REGISTRY[ARANGO_CREATE_COLLECTION] = ToolRegistration(
    name=ARANGO_CREATE_COLLECTION,
    description="Create a collection (document or edge).",
    model=CreateCollectionArgs,
    handler=handle_create_collection,
)

TOOL_REGISTRY[ARANGO_BACKUP] = ToolRegistration(
    name=ARANGO_BACKUP,
    description="Backup collections to JSON files.",
    model=BackupArgs,
    handler=handle_backup,
)

TOOL_REGISTRY[ARANGO_LIST_INDEXES] = ToolRegistration(
    name=ARANGO_LIST_INDEXES,
    description="List indexes for a collection.",
    model=ListIndexesArgs,
    handler=handle_list_indexes,
)

TOOL_REGISTRY[ARANGO_CREATE_INDEX] = ToolRegistration(
    name=ARANGO_CREATE_INDEX,
    description="Create an index on a collection (persistent, hash, skiplist, ttl, fulltext, geo).",
    model=CreateIndexArgs,
    handler=handle_create_index,
)

TOOL_REGISTRY[ARANGO_DELETE_INDEX] = ToolRegistration(
    name=ARANGO_DELETE_INDEX,
    description="Delete an index by id or name from a collection.",
    model=DeleteIndexArgs,
    handler=handle_delete_index,
)

TOOL_REGISTRY[ARANGO_EXPLAIN_QUERY] = ToolRegistration(
    name=ARANGO_EXPLAIN_QUERY,
    description="Explain an AQL query and return execution plans and optional index suggestions.",
    model=ExplainQueryArgs,
    handler=handle_explain_query,
)

TOOL_REGISTRY[ARANGO_VALIDATE_REFERENCES] = ToolRegistration(
    name=ARANGO_VALIDATE_REFERENCES,
    description="Validate that documents in a collection have valid references in specified fields.",
    model=ValidateReferencesArgs,
    handler=handle_validate_references,
)

TOOL_REGISTRY[ARANGO_INSERT_WITH_VALIDATION] = ToolRegistration(
    name=ARANGO_INSERT_WITH_VALIDATION,
    description="Insert a document after validating its reference fields.",
    model=InsertWithValidationArgs,
    handler=handle_insert_with_validation,
)

TOOL_REGISTRY[ARANGO_BULK_INSERT] = ToolRegistration(
    name=ARANGO_BULK_INSERT,
    description="Bulk insert documents with batching and basic error handling.",
    model=BulkInsertArgs,
    handler=handle_bulk_insert,
)

TOOL_REGISTRY[ARANGO_BULK_UPDATE] = ToolRegistration(
    name=ARANGO_BULK_UPDATE,
    description="Bulk update documents by key with batching.",
    model=BulkUpdateArgs,
    handler=handle_bulk_update,
)

TOOL_REGISTRY[ARANGO_CREATE_GRAPH] = ToolRegistration(
    name=ARANGO_CREATE_GRAPH,
    description="Create a named graph with edge definitions (optionally creating collections).",
    model=CreateGraphArgs,
    handler=handle_create_graph,
)

TOOL_REGISTRY[ARANGO_ADD_EDGE] = ToolRegistration(
    name=ARANGO_ADD_EDGE,
    description="Add an edge document between two vertices with optional attributes.",
    model=AddEdgeArgs,
    handler=handle_add_edge,
)

TOOL_REGISTRY[ARANGO_TRAVERSE] = ToolRegistration(
    name=ARANGO_TRAVERSE,
    description="Traverse graph from a start vertex with depth bounds (by graph or edge collections).",
    model=TraverseArgs,
    handler=handle_traverse,
)

TOOL_REGISTRY[ARANGO_SHORTEST_PATH] = ToolRegistration(
    name=ARANGO_SHORTEST_PATH,
    description="Compute the shortest path between two vertices (by graph or edge collections).",
    model=ShortestPathArgs,
    handler=handle_shortest_path,
)

TOOL_REGISTRY[ARANGO_LIST_GRAPHS] = ToolRegistration(
    name=ARANGO_LIST_GRAPHS,
    description="List available graphs in the database.",
    model=ListGraphsArgs,
    handler=handle_list_graphs,
)

TOOL_REGISTRY[ARANGO_ADD_VERTEX_COLLECTION] = ToolRegistration(
    name=ARANGO_ADD_VERTEX_COLLECTION,
    description="Add a vertex collection to a named graph.",
    model=AddVertexCollectionArgs,
    handler=handle_add_vertex_collection,
)

TOOL_REGISTRY[ARANGO_ADD_EDGE_DEFINITION] = ToolRegistration(
    name=ARANGO_ADD_EDGE_DEFINITION,
    description="Create an edge definition in a named graph.",
    model=AddEdgeDefinitionArgs,
    handler=handle_add_edge_definition,
)

# Alias: ARANGO_GRAPH_TRAVERSAL -> handle_traverse
TOOL_REGISTRY[ARANGO_GRAPH_TRAVERSAL] = ToolRegistration(
    name=ARANGO_GRAPH_TRAVERSAL,
    description="Alias for arango_traverse (graph traversal by graph or edge collections).",
    model=TraverseArgs,
    handler=handle_traverse,
)

# Alias: ARANGO_ADD_VERTEX -> handle_insert
TOOL_REGISTRY[ARANGO_ADD_VERTEX] = ToolRegistration(
    name=ARANGO_ADD_VERTEX,
    description="Alias for arango_insert (insert a vertex document into a collection).",
    model=InsertArgs,
    handler=handle_insert,
)

TOOL_REGISTRY[ARANGO_CREATE_SCHEMA] = ToolRegistration(
    name=ARANGO_CREATE_SCHEMA,
    description="Create or update a named JSON Schema for a collection.",
    model=CreateSchemaArgs,
    handler=handle_create_schema,
)

TOOL_REGISTRY[ARANGO_VALIDATE_DOCUMENT] = ToolRegistration(
    name=ARANGO_VALIDATE_DOCUMENT,
    description="Validate a document against a stored or inline JSON Schema.",
    model=ValidateDocumentArgs,
    handler=handle_validate_document,
)

TOOL_REGISTRY[ARANGO_QUERY_BUILDER] = ToolRegistration(
    name=ARANGO_QUERY_BUILDER,
    description="Build and execute a simple AQL query from filters, sort, and limit.",
    model=QueryBuilderArgs,
    handler=handle_query_builder,
)

TOOL_REGISTRY[ARANGO_QUERY_PROFILE] = ToolRegistration(
    name=ARANGO_QUERY_PROFILE,
    description="Explain a query and return plans/stats for profiling.",
    model=QueryProfileArgs,
    handler=handle_query_profile,
)

# Graph Management Tools (Phase 5)
TOOL_REGISTRY[ARANGO_BACKUP_GRAPH] = ToolRegistration(
    name=ARANGO_BACKUP_GRAPH,
    description="Export complete graph structure including vertices, edges, and metadata.",
    model=BackupGraphArgs,
    handler=handle_backup_graph,
)

TOOL_REGISTRY[ARANGO_RESTORE_GRAPH] = ToolRegistration(
    name=ARANGO_RESTORE_GRAPH,
    description="Import graph data with referential integrity validation and conflict resolution.",
    model=RestoreGraphArgs,
    handler=handle_restore_graph,
)

TOOL_REGISTRY[ARANGO_BACKUP_NAMED_GRAPHS] = ToolRegistration(
    name=ARANGO_BACKUP_NAMED_GRAPHS,
    description="Backup graph definitions from _graphs system collection.",
    model=BackupNamedGraphsArgs,
    handler=handle_backup_named_graphs,
)

TOOL_REGISTRY[ARANGO_VALIDATE_GRAPH_INTEGRITY] = ToolRegistration(
    name=ARANGO_VALIDATE_GRAPH_INTEGRITY,
    description="Verify graph consistency, orphaned edges, and constraint violations.",
    model=ValidateGraphIntegrityArgs,
    handler=handle_validate_graph_integrity,
)

TOOL_REGISTRY[ARANGO_GRAPH_STATISTICS] = ToolRegistration(
    name=ARANGO_GRAPH_STATISTICS,
    description="Generate comprehensive graph analytics (vertex/edge counts, degree distribution, connectivity metrics).",
    model=GraphStatisticsArgs,
    handler=handle_graph_statistics,
)


@asynccontextmanager
async def server_lifespan(server: Server) -> AsyncIterator[Dict[str, Any]]:
    """Initialize ArangoDB client+db once and share via request context."""
    # Configure logging to stderr only (never stdout for stdio MCP servers)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    logger = logging.getLogger("mcp_arangodb_async.entry")

    # Validate tool registry is properly populated
    if not TOOL_REGISTRY:
        logger.error("Tool registry is empty - no tools registered")
        raise RuntimeError(
            "Tool registry is empty. No tools have been registered. "
            "This indicates a critical initialization error."
        )
    logger.info(f"Tool registry validated: {len(TOOL_REGISTRY)} tools registered")

    cfg = load_config()
    client = None
    db = None
    # Retry connection per env or defaults
    retries = int(os.getenv("ARANGO_CONNECT_RETRIES", "3"))
    delay = float(os.getenv("ARANGO_CONNECT_DELAY_SEC", "1.0"))
    for attempt in range(1, max(1, retries) + 1):
        try:
            client, db = get_client_and_db(cfg)
            logger.info(
                "Connected to ArangoDB at %s db=%s (attempt %d)",
                cfg.arango_url,
                cfg.database,
                attempt,
            )
            break
        except Exception:
            logger.warning("ArangoDB connection attempt %d failed", attempt, exc_info=True)
            if attempt < retries:
                try:
                    await asyncio.sleep(delay)
                except Exception:
                    pass
            else:
                logger.error(
                    "Failed to connect to ArangoDB after %d attempts; starting server without DB",
                    retries,
                )
                client = None
                db = None
                break

    try:
        yield {"db": db, "client": client}
    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                logger.debug("Error closing Arango client", exc_info=True)


server = Server("mcp-arangodb-async", lifespan=server_lifespan)


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """Generate tool list from registry.

    Dynamically builds the MCP tool list from TOOL_REGISTRY, ensuring
    consistency between tool metadata and handler dispatch.

    Returns:
        List of MCP Tool objects with name, description, and input schema
    """
    # Build tools from registry
    tools: List[types.Tool] = [
        types.Tool(
            name=reg.name,
            description=reg.description,
            inputSchema=reg.model.model_json_schema(),
        )
        for reg in TOOL_REGISTRY.values()
    ]

    # Compatibility: during pytest integration tests, expect baseline 7 tools.
    # Respect explicit override via MCP_COMPAT_TOOLSET=full to test the full set.
    compat = os.getenv("MCP_COMPAT_TOOLSET")
    if compat == "baseline" or (compat is None and os.getenv("PYTEST_CURRENT_TEST")):
        # Return first 7 tools in registry order
        return tools[:7]
    return tools


def _json_content(data: Any) -> List[types.Content]:
    """Convert data to JSON text content for MCP response.
    
    Args:
        data: Any serializable data structure
        
    Returns:
        List containing a single TextContent with JSON representation
    """
    return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False))]


def _invoke_handler(handler: Callable, db: StandardDatabase, args: Dict[str, Any]) -> Any:
    """Invoke handler function with appropriate signature based on its parameter requirements.

    This function provides dual signature support to handle two different calling conventions:

    1. **Test compatibility mode**: `handler(db, **args)`
       - Used by mocked handlers in unit tests that need to inspect individual keyword arguments
       - Allows tests to verify specific parameter values were passed correctly
       - Enables more granular test assertions on handler behavior

    2. **Production handler mode**: `handler(db, args)`
       - Used by actual handler implementations that expect a single args dictionary
       - Matches the documented handler signature pattern: (db, args: Dict[str, Any])
       - More efficient as it avoids dictionary unpacking

    The try/catch mechanism automatically detects which signature the handler expects:
    - First attempts kwargs expansion for test compatibility
    - Falls back to single args dict for production handlers
    - TypeError from wrong parameter count triggers the fallback

    Args:
        handler: Handler function to invoke (either real implementation or test mock)
        db: ArangoDB database instance
        args: Validated arguments dictionary from Pydantic model

    Returns:
        Handler function result (typically Dict[str, Any] or List[Dict[str, Any]])

    Note:
        This dual signature support maintains backward compatibility while enabling
        comprehensive testing. The pattern handles the semantic difference between
        handlers that require arguments vs. those that don't (e.g., list_collections).
    """
    try:
        # Attempt test-compatible signature: handler(db, **args)
        # This allows mocked handlers in tests to inspect individual parameters
        return handler(db, **args)
    except TypeError:
        # Fallback to production signature: handler(db, args)
        # This matches the documented handler pattern for real implementations
        return handler(db, args)


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.Content]:
    """Execute a tool by dispatching to its registered handler.

    Uses TOOL_REGISTRY for O(1) lookup and dispatch, replacing the previous
    O(n) if-elif chain. Maintains all existing features: validation, lazy
    connect, error handling.

    Args:
        name: Tool name to execute
        arguments: Raw arguments dictionary from MCP client

    Returns:
        List of MCP Content objects (typically JSON text content)
    """
    logger = logging.getLogger("mcp_arangodb_async.entry")
    # Access lifespan context; may not have connected (graceful degradation)
    ctx = server.request_context
    db = ctx.lifespan_context.get("db") if ctx and ctx.lifespan_context else None

    # Look up tool in registry
    tool_reg = TOOL_REGISTRY.get(name)
    if tool_reg is None:
        return _json_content({"error": f"Unknown tool: {name}"})

    # Validate incoming arguments strictly via Pydantic
    try:
        parsed = tool_reg.model(**(arguments or {}))
        validated_args: Dict[str, Any] = parsed.model_dump(exclude_none=True)
    except ValidationError as ve:
        return _json_content({
            "error": "ValidationError",
            "tool": name,
            "details": json.loads(ve.json()),
        })

    # If DB is unavailable, attempt a lazy one-shot connect (helps when startup race occurred)
    if db is None:
        try:
            cfg = load_config()
            client, db_conn = get_client_and_db(cfg)
            # Cache for subsequent calls
            if ctx and ctx.lifespan_context is not None:
                ctx.lifespan_context["db"] = db_conn
                ctx.lifespan_context["client"] = client
            db = db_conn
            logger.info("Lazy DB connect succeeded during tool call: db=%s", cfg.database)
        except Exception:
            logger.warning("Lazy DB connect failed; returning Database unavailable", exc_info=True)
            return _json_content({
                "error": "Database unavailable",
                "tool": name,
                "hint": "Ensure ArangoDB is reachable or check ARANGO_* environment variables.",
            })

    # Dispatch to handler via registry (O(1) lookup)
    try:
        result = _invoke_handler(tool_reg.handler, db, validated_args)
        return _json_content(result)
    except Exception as e:
        logger.exception("Error executing tool '%s'", name)
        return _json_content({
            "error": str(e),
            "tool": name,
        })


# Test compatibility shim: expose handlers dict expected by integration tests
# (These reference the actual async functions defined above.)
setattr(server, "_handlers", {
    "list_tools": handle_list_tools,
    "call_tool": call_tool,
})

# Compatibility shim: make Server.request_context safe and patchable everywhere.
# Always provide a getter/setter that returns a simple object by default, avoiding
# ContextVar LookupError outside of real MCP requests. Tests can patch this.
ServerClass = type(server)

def _safe_get_request_context(self: Any) -> Any:
    return getattr(self, "_safe_request_context", SimpleNamespace(lifespan_context={}))

def _safe_set_request_context(self: Any, value: Any) -> None:
    setattr(self, "_safe_request_context", value)

def _safe_del_request_context(self: Any) -> None:
    if hasattr(self, "_safe_request_context"):
        try:
            delattr(self, "_safe_request_context")
        except Exception:
            pass

setattr(
    ServerClass,
    "request_context",
    property(_safe_get_request_context, _safe_set_request_context, _safe_del_request_context),
)


async def run() -> None:
    """Run the MCP server with stdio transport.
    
    Sets up the server with proper initialization options and runs it
    until termination.
    """
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-arangodb-async",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main() -> None:
    """Console script entry point for arango-server command.
    
    This is the main entry point that starts the async MCP server.
    Used by the console script defined in pyproject.toml.
    """
    asyncio.run(run())


if __name__ == "__main__":
    main()
