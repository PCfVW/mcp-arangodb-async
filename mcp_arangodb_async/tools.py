"""
ArangoDB MCP Server - Tool Name Constants

Purpose:
    Centralized definitions for all MCP tool names. This ensures consistent
    usage across tool registration, validation, and dispatch.

Constants by category:

Core Data Tools:
    - ARANGO_QUERY
    - ARANGO_LIST_COLLECTIONS
    - ARANGO_INSERT
    - ARANGO_UPDATE
    - ARANGO_REMOVE
    - ARANGO_CREATE_COLLECTION
    - ARANGO_BACKUP

Indexing & Query Analysis:
    - ARANGO_LIST_INDEXES
    - ARANGO_CREATE_INDEX
    - ARANGO_DELETE_INDEX
    - ARANGO_EXPLAIN_QUERY

Validation & Bulk Ops:
    - ARANGO_VALIDATE_REFERENCES
    - ARANGO_INSERT_WITH_VALIDATION
    - ARANGO_BULK_INSERT
    - ARANGO_BULK_UPDATE

Graph Tools:
    - ARANGO_CREATE_GRAPH
    - ARANGO_ADD_EDGE
    - ARANGO_TRAVERSE
    - ARANGO_SHORTEST_PATH
    - ARANGO_LIST_GRAPHS
    - ARANGO_ADD_VERTEX_COLLECTION
    - ARANGO_ADD_EDGE_DEFINITION
    - ARANGO_GRAPH_TRAVERSAL (alias of ARANGO_TRAVERSE)
    - ARANGO_ADD_VERTEX (alias of ARANGO_INSERT)

Graph Management Tools:
    - ARANGO_BACKUP_GRAPH
    - ARANGO_RESTORE_GRAPH
    - ARANGO_BACKUP_NAMED_GRAPHS
    - ARANGO_VALIDATE_GRAPH_INTEGRITY
    - ARANGO_GRAPH_STATISTICS

Schema & Enhanced Query Tools:
    - ARANGO_CREATE_SCHEMA
    - ARANGO_VALIDATE_DOCUMENT
    - ARANGO_QUERY_BUILDER
    - ARANGO_QUERY_PROFILE
"""

# Tool name constants (to match the TS implementation semantics)
ARANGO_QUERY = "arango_query"
ARANGO_LIST_COLLECTIONS = "arango_list_collections"
ARANGO_INSERT = "arango_insert"
ARANGO_UPDATE = "arango_update"
ARANGO_REMOVE = "arango_remove"
ARANGO_BACKUP = "arango_backup"
ARANGO_CREATE_COLLECTION = "arango_create_collection"
ARANGO_LIST_INDEXES = "arango_list_indexes"
ARANGO_CREATE_INDEX = "arango_create_index"
ARANGO_DELETE_INDEX = "arango_delete_index"
ARANGO_EXPLAIN_QUERY = "arango_explain_query"
ARANGO_VALIDATE_REFERENCES = "arango_validate_references"
ARANGO_INSERT_WITH_VALIDATION = "arango_insert_with_validation"
ARANGO_BULK_INSERT = "arango_bulk_insert"
ARANGO_BULK_UPDATE = "arango_bulk_update"

# Graph tools (Phase 2)
ARANGO_CREATE_GRAPH = "arango_create_graph"
ARANGO_ADD_EDGE = "arango_add_edge"
ARANGO_TRAVERSE = "arango_traverse"
ARANGO_SHORTEST_PATH = "arango_shortest_path"

# Additional graph management tools
ARANGO_LIST_GRAPHS = "arango_list_graphs"
ARANGO_ADD_VERTEX_COLLECTION = "arango_add_vertex_collection"
ARANGO_ADD_EDGE_DEFINITION = "arango_add_edge_definition"

# Alias for traversal to match requested name
ARANGO_GRAPH_TRAVERSAL = "arango_graph_traversal"

# Alias for vertex insertion (reuses InsertArgs and handle_insert)
ARANGO_ADD_VERTEX = "arango_add_vertex"

# Schema management tools
ARANGO_CREATE_SCHEMA = "arango_create_schema"
ARANGO_VALIDATE_DOCUMENT = "arango_validate_document"

# Enhanced query tools
ARANGO_QUERY_BUILDER = "arango_query_builder"
ARANGO_QUERY_PROFILE = "arango_query_profile"

# Graph Management Tools (Phase 5 - New Graph Tools)
ARANGO_BACKUP_GRAPH = "arango_backup_graph"
ARANGO_RESTORE_GRAPH = "arango_restore_graph"
ARANGO_BACKUP_NAMED_GRAPHS = "arango_backup_named_graphs"
ARANGO_VALIDATE_GRAPH_INTEGRITY = "arango_validate_graph_integrity"
ARANGO_GRAPH_STATISTICS = "arango_graph_statistics"

# Database Status Tool
ARANGO_DATABASE_STATUS = "arango_database_status"

# Pattern 1: Progressive Tool Discovery
ARANGO_SEARCH_TOOLS = "arango_search_tools"
ARANGO_LIST_TOOLS_BY_CATEGORY = "arango_list_tools_by_category"

# Pattern 2: Context Switching
ARANGO_SWITCH_CONTEXT = "arango_switch_context"
ARANGO_GET_ACTIVE_CONTEXT = "arango_get_active_context"
ARANGO_LIST_CONTEXTS = "arango_list_contexts"

# Pattern 3: Tool Unloading
ARANGO_ADVANCE_WORKFLOW_STAGE = "arango_advance_workflow_stage"
ARANGO_GET_TOOL_USAGE_STATS = "arango_get_tool_usage_stats"
ARANGO_UNLOAD_TOOLS = "arango_unload_tools"
