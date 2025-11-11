# Tools Reference

Complete documentation for all 43 MCP tools provided by the mcp-arangodb-async server.

**Audience:** End Users and Developers
**Prerequisites:** Server installed and configured
**Estimated Time:** Reference document (browse as needed)

---

## Table of Contents

1. [Overview](#overview)
2. [Core Data Operations (7)](#core-data-operations-7)
3. [Indexing & Query Analysis (4)](#indexing--query-analysis-4)
4. [Validation & Bulk Operations (4)](#validation--bulk-operations-4)
5. [Schema Management (2)](#schema-management-2)
6. [Enhanced Query Tools (2)](#enhanced-query-tools-2)
7. [Basic Graph Operations (7)](#basic-graph-operations-7)
8. [Advanced Graph Management (5)](#advanced-graph-management-5)
9. [Tool Aliases (2)](#tool-aliases-2)
10. [Health & Status (1)](#health--status-1)
11. [MCP Design Pattern Tools (9)](#mcp-design-pattern-tools-9)
12. [Toolset Configuration](#toolset-configuration)

---

## Overview

The mcp-arangodb-async server provides **43 comprehensive tools** organized into logical categories. Each tool:
- Uses **strict Pydantic validation** for arguments
- Provides **consistent error handling** with detailed messages
- Returns **JSON-serializable results** for easy integration
- Follows **standard handler signature**: `(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]`

### Tool Categories

| Category | Tools | Use Cases |
|----------|-------|-----------|
| **Core Data Operations** | 7 | Basic CRUD, queries, backups |
| **Indexing & Query Analysis** | 4 | Performance optimization, query profiling |
| **Validation & Bulk Operations** | 4 | Data integrity, batch processing |
| **Schema Management** | 2 | JSON Schema validation |
| **Enhanced Query Tools** | 2 | Query building, profiling |
| **Basic Graph Operations** | 7 | Graph creation, traversal, shortest path |
| **Advanced Graph Management** | 5 | Graph backup/restore, integrity validation, analytics |
| **Tool Aliases** | 2 | Convenience aliases for common operations |
| **Health & Status** | 1 | Server health checks |
| **MCP Design Pattern Tools** | 9 | Progressive discovery, context switching, tool unloading |

---

## Core Data Operations (7)

### arango_query

Execute AQL (ArangoDB Query Language) queries with optional bind variables.

**Parameters:**
- `query` (string, required) - AQL query string
- `bind_vars` (object, optional) - Bind variables for parameterized queries

**Returns:**
- Array of result documents

**Example:**
```json
{
  "query": "FOR doc IN users FILTER doc.age > @minAge RETURN doc",
  "bind_vars": {"minAge": 18}
}
```

**Result:**
```json
[
  {"_key": "123", "_id": "users/123", "name": "Alice", "age": 25},
  {"_key": "456", "_id": "users/456", "name": "Bob", "age": 30}
]
```

**Use Cases:**
- Complex data retrieval
- Aggregations and analytics
- Graph traversals (when combined with graph syntax)
- Data transformations

**Best Practices:**
- Always use bind variables for dynamic values (prevents AQL injection)
- Test queries in ArangoDB web UI first (http://localhost:8529)
- Use `LIMIT` clause for large result sets
- Consider creating indexes for frequently filtered fields

---

### arango_list_collections

List all non-system collections in the database.

**Parameters:**
- None (empty object or omitted)

**Returns:**
- Array of collection names (strings)

**Example:**
```json
{}
```

**Result:**
```json
["users", "products", "orders", "follows"]
```

**Use Cases:**
- Database exploration
- Validation before operations
- Dynamic collection discovery
- Backup preparation

---

### arango_insert

Insert a document into a collection.

**Parameters:**
- `collection` (string, required) - Collection name
- `document` (object, required) - Document to insert
- `return_new` (boolean, optional, default: true) - Return inserted document

**Returns:**
- Inserted document with `_key`, `_id`, `_rev` fields

**Example:**
```json
{
  "collection": "users",
  "document": {"name": "Alice", "email": "alice@example.com", "age": 25}
}
```

**Result:**
```json
{
  "_key": "123456",
  "_id": "users/123456",
  "_rev": "_abc123def",
  "name": "Alice",
  "email": "alice@example.com",
  "age": 25
}
```

**Use Cases:**
- Adding new records
- Creating vertices in graphs
- Inserting test data
- User registration

**Best Practices:**
- Let ArangoDB generate `_key` automatically (unless you need specific keys)
- Use `arango_insert_with_validation` for documents with references
- Consider `arango_bulk_insert` for multiple documents

---

### arango_update

Update an existing document by key.

**Parameters:**
- `collection` (string, required) - Collection name
- `key` (string, required) - Document key
- `document` (object, required) - Fields to update (partial update)
- `return_new` (boolean, optional, default: true) - Return updated document

**Returns:**
- Updated document with new `_rev`

**Example:**
```json
{
  "collection": "users",
  "key": "123456",
  "document": {"age": 26, "updated_at": "2024-01-01T12:00:00Z"}
}
```

**Result:**
```json
{
  "_key": "123456",
  "_id": "users/123456",
  "_rev": "_xyz789ghi",
  "name": "Alice",
  "email": "alice@example.com",
  "age": 26,
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Use Cases:**
- Modifying existing records
- Updating user profiles
- Incrementing counters
- Timestamping changes

**Best Practices:**
- Only include fields to update (partial updates are more efficient)
- Use `arango_bulk_update` for multiple documents
- Consider using AQL `UPDATE` for complex conditional updates

---

### arango_remove

Remove a document by key from a collection.

**Parameters:**
- `collection` (string, required) - Collection name
- `key` (string, required) - Document key to remove

**Returns:**
- Confirmation object with removed document metadata

**Example:**
```json
{
  "collection": "users",
  "key": "123456"
}
```

**Result:**
```json
{
  "_key": "123456",
  "_id": "users/123456",
  "_rev": "_xyz789ghi"
}
```

**Use Cases:**
- Deleting records
- Removing test data
- User account deletion
- Data cleanup

**Best Practices:**
- Verify document exists before removal
- Consider soft deletes (update with `deleted: true`) for audit trails
- Use AQL `REMOVE` for conditional or bulk deletions

---

### arango_create_collection

Create a new collection or return properties of existing collection.

**Parameters:**
- `name` (string, required) - Collection name
- `type` (string, optional, default: "document") - Collection type: "document" or "edge"
- `wait_for_sync` (boolean, optional, default: false) - Synchronous writes

**Returns:**
- Collection properties object

**Example:**
```json
{
  "name": "products",
  "type": "document",
  "wait_for_sync": false
}
```

**Result:**
```json
{
  "name": "products",
  "type": "document",
  "waitForSync": false
}
```

**Use Cases:**
- Database initialization
- Dynamic collection creation
- Graph setup (edge collections)
- Test environment preparation

**Best Practices:**
- Use `type: "edge"` for graph relationships
- Set `wait_for_sync: true` for critical data (slower but safer)
- Check if collection exists first with `arango_list_collections`

---

## Indexing & Query Analysis (4)

### arango_list_indexes

List all indexes for a collection.

**Parameters:**
- `collection` (string, required) - Collection name

**Returns:**
- Array of index objects with type, fields, and properties

**Example:**
```json
{"collection": "users"}
```

**Result:**
```json
[
  {"id": "users/0", "type": "primary", "fields": ["_key"], "unique": true},
  {"id": "users/123", "type": "hash", "fields": ["email"], "unique": true}
]
```

---

### arango_create_index

Create an index on a collection.

**Parameters:**
- `collection` (string, required) - Collection name
- `type` (string, required) - Index type: "persistent", "hash", "skiplist", "ttl", "fulltext", "geo"
- `fields` (array of strings, required) - Fields to index
- `unique` (boolean, optional, default: false) - Unique constraint
- `sparse` (boolean, optional, default: false) - Sparse index (skip null values)

**Returns:**
- Created index object

**Example:**
```json
{
  "collection": "users",
  "type": "hash",
  "fields": ["email"],
  "unique": true
}
```

**Use Cases:**
- Query performance optimization
- Enforcing uniqueness constraints
- Full-text search setup
- Geospatial queries

---

### arango_delete_index

Delete an index by ID or name.

**Parameters:**
- `collection` (string, required) - Collection name
- `index_id` (string, optional) - Index ID (e.g., "users/123")
- `index_name` (string, optional) - Index name

**Returns:**
- Confirmation object

---

### arango_explain_query

Explain AQL query execution plan.

**Parameters:**
- `query` (string, required) - AQL query
- `bind_vars` (object, optional) - Bind variables

**Returns:**
- Query execution plan, warnings, and statistics

**Use Cases:**
- Query optimization
- Performance troubleshooting
- Index usage verification

---

## Validation & Bulk Operations (4)

### arango_validate_references

Validate that reference fields point to existing documents.

**Parameters:**
- `collection` (string, required) - Collection to validate
- `reference_fields` (array of objects, required) - Reference field definitions
  - `field` (string) - Field name
  - `target_collection` (string) - Target collection

**Returns:**
- Validation report with invalid references

**Example:**
```json
{
  "collection": "orders",
  "reference_fields": [
    {"field": "user_id", "target_collection": "users"},
    {"field": "product_id", "target_collection": "products"}
  ]
}
```

---

### arango_insert_with_validation

Insert document after validating references.

**Parameters:**
- `collection` (string, required) - Collection name
- `document` (object, required) - Document to insert
- `reference_fields` (array of objects, required) - Reference field definitions

**Returns:**
- Inserted document or validation error

---

### arango_bulk_insert

Batch insert multiple documents.

**Parameters:**
- `collection` (string, required) - Collection name
- `documents` (array of objects, required) - Documents to insert

**Returns:**
- Insertion report with success/error counts

**Example:**
```json
{
  "collection": "users",
  "documents": [
    {"name": "Alice", "age": 25},
    {"name": "Bob", "age": 30},
    {"name": "Charlie", "age": 35}
  ]
}
```

**Result:**
```json
{
  "inserted": 3,
  "errors": 0,
  "collection": "users"
}
```

---

### arango_bulk_update

Batch update multiple documents by key.

**Parameters:**
- `collection` (string, required) - Collection name
- `updates` (array of objects, required) - Update operations
  - `key` (string) - Document key
  - `document` (object) - Fields to update

**Returns:**
- Update report with success/error counts

---

## Schema Management (2)

### arango_create_schema

Create or update a named JSON Schema.

**Parameters:**
- `schema_name` (string, required) - Schema identifier
- `schema` (object, required) - JSON Schema definition

**Returns:**
- Confirmation with schema name

**Example:**
```json
{
  "schema_name": "user_schema",
  "schema": {
    "type": "object",
    "properties": {
      "name": {"type": "string"},
      "age": {"type": "integer", "minimum": 0}
    },
    "required": ["name", "age"]
  }
}
```

---

### arango_validate_document

Validate a document against a stored or inline schema.

**Parameters:**
- `document` (object, required) - Document to validate
- `schema_name` (string, optional) - Stored schema name
- `schema` (object, optional) - Inline JSON Schema

**Returns:**
- Validation result with errors (if any)

---

## Enhanced Query Tools (2)

### arango_query_builder

Build and execute simple AQL queries from structured filters.

**Parameters:**
- `collection` (string, required) - Collection to query
- `filters` (object, optional) - Field filters
- `sort` (object, optional) - Sort specification
- `limit` (integer, optional) - Result limit

**Example:**
```json
{
  "collection": "users",
  "filters": {"age": {"$gt": 18}},
  "sort": {"age": "DESC"},
  "limit": 10
}
```

---

### arango_query_profile

Profile query execution with detailed statistics.

**Parameters:**
- `query` (string, required) - AQL query
- `bind_vars` (object, optional) - Bind variables

**Returns:**
- Execution plan, statistics, and optimization suggestions

---

## Basic Graph Operations (7)

### arango_create_graph

Create a named graph with edge definitions.

**Parameters:**
- `name` (string, required) - Graph name
- `edge_definitions` (array of objects, required) - Edge definitions
  - `collection` (string) - Edge collection name
  - `from` (array of strings) - Source vertex collections
  - `to` (array of strings) - Target vertex collections
- `orphan_collections` (array of strings, optional) - Vertex collections without edges

**Returns:**
- Graph object with name and edge definitions

**Example:**
```json
{
  "name": "social_network",
  "edge_definitions": [
    {
      "collection": "follows",
      "from": ["users"],
      "to": ["users"]
    }
  ]
}
```

**Use Cases:**
- Social networks (users, follows, likes)
- Dependency graphs (modules, imports)
- Knowledge graphs (entities, relationships)
- Organizational hierarchies

---

### arango_add_edge

Insert an edge between two vertices.

**Parameters:**
- `collection` (string, required) - Edge collection name
- `from` (string, required) - Source vertex ID (e.g., "users/123")
- `to` (string, required) - Target vertex ID (e.g., "users/456")
- `attributes` (object, optional) - Additional edge attributes

**Returns:**
- Inserted edge with `_key`, `_id`, `_rev`, `_from`, `_to`

**Example:**
```json
{
  "collection": "follows",
  "from": "users/alice",
  "to": "users/bob",
  "attributes": {"since": "2024-01-01", "weight": 1.0}
}
```

---

### arango_traverse

Traverse a graph from a start vertex.

**Parameters:**
- `start_vertex` (string, required) - Starting vertex ID
- `graph_name` (string, optional) - Named graph to traverse
- `edge_collection` (string, optional) - Edge collection (if not using named graph)
- `direction` (string, optional, default: "outbound") - "outbound", "inbound", or "any"
- `min_depth` (integer, optional, default: 1) - Minimum traversal depth
- `max_depth` (integer, optional, default: 1) - Maximum traversal depth

**Returns:**
- Array of visited vertices and edges

**Example:**
```json
{
  "start_vertex": "users/alice",
  "graph_name": "social_network",
  "direction": "outbound",
  "max_depth": 2
}
```

**Use Cases:**
- Finding friends of friends
- Dependency resolution
- Reachability analysis
- Network exploration

---

### arango_shortest_path

Compute shortest path between two vertices.

**Parameters:**
- `start_vertex` (string, required) - Starting vertex ID
- `target_vertex` (string, required) - Target vertex ID
- `graph_name` (string, optional) - Named graph
- `edge_collection` (string, optional) - Edge collection (if not using named graph)
- `direction` (string, optional, default: "outbound") - Traversal direction

**Returns:**
- Path object with vertices and edges

**Example:**
```json
{
  "start_vertex": "users/alice",
  "target_vertex": "users/charlie",
  "graph_name": "social_network"
}
```

**Result:**
```json
{
  "vertices": [
    {"_id": "users/alice", "name": "Alice"},
    {"_id": "users/bob", "name": "Bob"},
    {"_id": "users/charlie", "name": "Charlie"}
  ],
  "edges": [
    {"_id": "follows/1", "_from": "users/alice", "_to": "users/bob"},
    {"_id": "follows/2", "_from": "users/bob", "_to": "users/charlie"}
  ],
  "distance": 2
}
```

---

### arango_list_graphs

List all named graphs in the database.

**Parameters:**
- None

**Returns:**
- Array of graph names

**Example:**
```json
{}
```

**Result:**
```json
["social_network", "dependency_graph", "knowledge_graph"]
```

---

### arango_add_vertex_collection

Add a vertex collection to an existing graph.

**Parameters:**
- `graph_name` (string, required) - Graph name
- `collection` (string, required) - Vertex collection to add

**Returns:**
- Updated graph object

---

### arango_add_edge_definition

Add an edge definition to an existing graph.

**Parameters:**
- `graph_name` (string, required) - Graph name
- `edge_definition` (object, required) - Edge definition
  - `collection` (string) - Edge collection name
  - `from` (array of strings) - Source vertex collections
  - `to` (array of strings) - Target vertex collections

**Returns:**
- Updated graph object

---

## Advanced Graph Management (5)

### arango_backup_graph

Export complete graph structure including vertices, edges, and metadata.

**Parameters:**
- `graph_name` (string, required) - Name of the graph to backup
- `output_dir` (string, optional) - Directory for backup files (auto-generated if not provided)
- `include_metadata` (boolean, optional, default: true) - Include graph metadata
- `doc_limit` (integer, optional) - Limit documents per collection

**Returns:**
- Backup report with file paths and counts

**Example:**
```json
{
  "graph_name": "social_network",
  "output_dir": "/tmp/graph_backup",
  "include_metadata": true
}
```

**Result:**
```json
{
  "graph_name": "social_network",
  "output_dir": "/tmp/graph_backup",
  "vertex_files": [{"collection": "users", "count": 1000, "file": "vertices/users.json"}],
  "edge_files": [{"collection": "follows", "count": 2500, "file": "edges/follows.json"}],
  "total_vertex_collections": 1,
  "total_edge_collections": 1,
  "total_documents": 3500,
  "metadata_included": true
}
```

---

### arango_restore_graph

Import graph data with referential integrity validation.

**Parameters:**
- `input_dir` (string, required) - Directory containing graph backup files
- `graph_name` (string, optional) - Name for restored graph (uses original if not provided)
- `conflict_resolution` (string, optional, default: "error") - "skip", "overwrite", or "error"
- `validate_integrity` (boolean, optional, default: true) - Validate referential integrity

**Returns:**
- Restore report with success/error counts

---

### arango_backup_named_graphs

Backup graph definitions from _graphs system collection.

**Parameters:**
- `output_file` (string, optional) - Output JSON file path
- `graph_names` (array of strings, optional) - Specific graphs to backup

**Returns:**
- Backup report with file path and graph count

---

### arango_validate_graph_integrity

Verify graph consistency and find orphaned edges.

**Parameters:**
- `graph_name` (string, optional) - Specific graph to validate (all if not provided)
- `check_orphaned_edges` (boolean, optional, default: true) - Check for edges with missing vertices
- `check_constraints` (boolean, optional, default: true) - Validate graph constraints
- `return_details` (boolean, optional, default: false) - Return detailed violation information

**Returns:**
- Validation report with orphaned edges and constraint violations

**Example:**
```json
{
  "graph_name": "social_network",
  "check_orphaned_edges": true,
  "return_details": true
}
```

**Result:**
```json
{
  "valid": false,
  "graphs_checked": 1,
  "total_orphaned_edges": 5,
  "total_constraint_violations": 0,
  "results": [{
    "graph_name": "social_network",
    "valid": false,
    "orphaned_edges_count": 5,
    "orphaned_edges": [{"_id": "follows/123", "_from": "users/deleted", "_to": "users/456"}]
  }],
  "summary": "Checked 1 graphs: 5 orphaned edges, 0 violations"
}
```

---

### arango_graph_statistics

Generate comprehensive graph analytics.

**Parameters:**
- `graph_name` (string, optional) - Specific graph to analyze (all if not provided)
- `include_degree_distribution` (boolean, optional, default: true) - Calculate degree distribution
- `include_connectivity` (boolean, optional, default: true) - Calculate connectivity metrics
- `sample_size` (integer, optional, minimum: 100) - Sample size for connectivity analysis

**Returns:**
- Graph statistics including vertex/edge counts, degree distribution, connectivity metrics

**Example:**
```json
{
  "graph_name": "social_network",
  "include_degree_distribution": true,
  "include_connectivity": true,
  "sample_size": 100
}
```

**Result:**
```json
{
  "graphs_analyzed": 1,
  "statistics": [{
    "graph_name": "social_network",
    "vertex_collections": ["users"],
    "edge_collections": ["follows"],
    "total_vertices": 1000,
    "total_edges": 2500,
    "density": 0.0025,
    "out_degree_distribution": [{"degree": 1, "frequency": 300}, {"degree": 2, "frequency": 250}],
    "max_out_degree": 50,
    "avg_out_degree": 2.5,
    "connectivity_sample_size": 100,
    "avg_reachable_vertices": 125.5,
    "max_reachable_vertices": 800
  }],
  "analysis_timestamp": "2024-01-01T12:00:00"
}
```

---

## Tool Aliases (2)

### arango_graph_traversal

Alias for `arango_traverse`. Provides the same functionality with an alternative name for clarity in graph workflows.

**Parameters:** Same as `arango_traverse`

---

### arango_add_vertex

Alias for `arango_insert`. Provides semantic clarity when inserting vertices in graph workflows.

**Parameters:** Same as `arango_insert`

---

## Health & Status (1)

### arango_database_status

Check database connectivity and return server information.

**Parameters:**
- None

**Returns:**
- Database status object with connection info

**Example:**
```json
{}
```

**Result:**
```json
{
  "ok": true,
  "db": "mcp_arangodb_test",
  "user": "mcp_arangodb_user",
  "version": "3.11.0"
}
```

---

## MCP Design Pattern Tools (9)

Tools for efficient MCP tool management through progressive discovery, context switching, and tool unloading patterns. These tools enable AI agents to reduce context window consumption by up to 98.7% when working with large tool sets.

**See Also:** [MCP Design Patterns Guide](./mcp-design-patterns.md) for comprehensive workflow examples and best practices.

### Pattern 1: Progressive Tool Discovery (2 tools)

#### arango_search_tools

Search for MCP tools by keywords and categories. Enables on-demand tool loading rather than loading all tools upfront.

**Parameters:**
- `keywords` (array of strings, required) - Keywords to search for in tool names and descriptions
- `categories` (array of strings, optional) - Filter by categories: `core_data`, `indexing`, `validation`, `schema`, `query`, `graph_basic`, `graph_advanced`, `aliases`, `health`, `mcp_patterns`
- `detail_level` (string, optional) - Level of detail: `name` (just names), `summary` (names + descriptions), `full` (complete schemas). Default: `summary`

**Returns:**
- `matches` (array) - Matching tools with requested detail level
- `total_matches` (integer) - Number of matching tools
- `keywords` (array) - Keywords used in search
- `categories_searched` (string or array) - Categories searched
- `detail_level` (string) - Detail level returned

**Example:**
```json
{
  "keywords": ["graph", "traverse"],
  "categories": ["graph_basic"],
  "detail_level": "summary"
}
```

**Result:**
```json
{
  "matches": [
    {
      "name": "arango_traverse",
      "description": "Traverse graph from a start vertex with depth bounds"
    },
    {
      "name": "arango_shortest_path",
      "description": "Compute the shortest path between two vertices"
    }
  ],
  "total_matches": 2,
  "keywords": ["graph", "traverse"],
  "categories_searched": ["graph_basic"],
  "detail_level": "summary"
}
```

**Use Cases:**
- Discover graph tools when building dependency graphs
- Find query optimization tools for performance analysis
- Locate validation tools for data integrity checks
- Search for backup tools before data migration

**Best Practices:**
- Start with `detail_level: "summary"` for initial discovery
- Use `detail_level: "full"` only when ready to execute
- Combine multiple keywords for precise results
- Filter by category to narrow search scope

---

#### arango_list_tools_by_category

List all MCP tools organized by category. Useful for understanding tool organization and selecting workflow-specific tool sets.

**Parameters:**
- `category` (string, optional) - Category to filter by. If not specified, returns all categories with their tools.

**Returns:**
- If category specified: `category`, `tools`, `tool_count`
- If no category: `categories` (object with all categories), `total_tools`

**Example:**
```json
{
  "category": "graph_basic"
}
```

**Result:**
```json
{
  "category": "graph_basic",
  "tools": [
    "arango_create_graph",
    "arango_list_graphs",
    "arango_add_vertex_collection",
    "arango_add_edge_definition",
    "arango_add_edge",
    "arango_traverse",
    "arango_shortest_path"
  ],
  "tool_count": 7
}
```

**Use Cases:**
- Understand tool organization before starting a workflow
- Explore available tools in a specific domain
- Build custom tool sets for specialized workflows
- Document available capabilities for team members

**Best Practices:**
- Call without parameters to see all categories first
- Use category filter to focus on specific domains
- Combine with `arango_search_tools` for precise discovery

---

### Pattern 2: Context Switching (3 tools)

#### arango_switch_context

Switch to a different workflow context with a predefined set of tools. Enables workflow-specific tool sets for different use cases.

**Parameters:**
- `context` (string, required) - Workflow context to switch to: `baseline`, `data_analysis`, `graph_modeling`, `bulk_operations`, `schema_validation`, `full`

**Returns:**
- `from_context` (string) - Previous context
- `to_context` (string) - New active context
- `description` (string) - Description of new context
- `tools_added` (array) - Tools added in new context
- `tools_removed` (array) - Tools removed from previous context
- `total_tools` (integer) - Total tools in new context
- `active_tools` (array) - All tools in new context

**Available Contexts:**
- `baseline` (7 tools) - Minimal CRUD operations for basic database interaction
- `data_analysis` (7 tools) - Query optimization and performance analysis
- `graph_modeling` (10 tools) - Graph creation, traversal, and analysis
- `bulk_operations` (6 tools) - Batch processing and bulk data operations
- `schema_validation` (6 tools) - Data integrity and schema management
- `full` (43 tools) - All available tools (fallback for complex workflows)

**Example:**
```json
{
  "context": "graph_modeling"
}
```

**Result:**
```json
{
  "from_context": "baseline",
  "to_context": "graph_modeling",
  "description": "Graph creation, traversal, and analysis",
  "tools_added": [
    "arango_create_graph",
    "arango_traverse",
    "arango_shortest_path"
  ],
  "tools_removed": [
    "arango_backup"
  ],
  "total_tools": 10,
  "active_tools": [
    "arango_create_graph",
    "arango_list_graphs",
    "arango_add_vertex_collection",
    "arango_add_edge_definition",
    "arango_add_edge",
    "arango_traverse",
    "arango_shortest_path",
    "arango_graph_statistics",
    "arango_validate_graph_integrity",
    "arango_query"
  ]
}
```

**Use Cases:**
- Switch to `graph_modeling` for dependency analysis
- Use `data_analysis` for query optimization workflows
- Switch to `bulk_operations` for data migration
- Use `schema_validation` for data integrity checks

**Best Practices:**
- Match context to workflow stage
- Minimize context switches (group related operations)
- Verify context before operations with `arango_get_active_context`
- Use `full` context only when truly needed

---

#### arango_get_active_context

Get the currently active workflow context and its tool set.

**Parameters:**
- None (empty object or omitted)

**Returns:**
- `active_context` (string) - Current context name
- `description` (string) - Context description
- `tools` (array) - Tools in current context
- `tool_count` (integer) - Number of tools

**Example:**
```json
{}
```

**Result:**
```json
{
  "active_context": "graph_modeling",
  "description": "Graph creation, traversal, and analysis",
  "tools": [
    "arango_create_graph",
    "arango_list_graphs",
    "arango_add_vertex_collection",
    "arango_add_edge_definition",
    "arango_add_edge",
    "arango_traverse",
    "arango_shortest_path",
    "arango_graph_statistics",
    "arango_validate_graph_integrity",
    "arango_query"
  ],
  "tool_count": 10
}
```

**Use Cases:**
- Verify current context before operations
- Debug workflow issues
- Log context state for audit trails
- Confirm successful context switches

---

#### arango_list_contexts

List all available workflow contexts with their descriptions and optional tool lists.

**Parameters:**
- `include_tools` (boolean, optional) - Include tool lists for each context. Default: `false`

**Returns:**
- `contexts` (object) - All available contexts with descriptions and tool counts
- `total_contexts` (integer) - Number of available contexts
- `active_context` (string) - Currently active context

**Example:**
```json
{
  "include_tools": false
}
```

**Result:**
```json
{
  "contexts": {
    "baseline": {
      "description": "Minimal CRUD operations for basic database interaction",
      "tool_count": 7
    },
    "data_analysis": {
      "description": "Query optimization and performance analysis",
      "tool_count": 7
    },
    "graph_modeling": {
      "description": "Graph creation, traversal, and analysis",
      "tool_count": 10
    },
    "bulk_operations": {
      "description": "Batch processing and bulk data operations",
      "tool_count": 6
    },
    "schema_validation": {
      "description": "Data integrity and schema management",
      "tool_count": 6
    },
    "full": {
      "description": "All available tools",
      "tool_count": 43
    }
  },
  "total_contexts": 6,
  "active_context": "baseline"
}
```

**Use Cases:**
- Explore available contexts before starting a workflow
- Document context options for team members
- Build custom context selection logic
- Understand tool organization by workflow type

---

### Pattern 3: Tool Unloading (4 tools)

#### arango_advance_workflow_stage

Advance to the next workflow stage, automatically unloading tools from previous stage and loading tools for new stage.

**Parameters:**
- `stage` (string, required) - Workflow stage to advance to: `setup`, `data_loading`, `analysis`, `cleanup`

**Returns:**
- `from_stage` (string or null) - Previous stage (null if first stage)
- `to_stage` (string) - New active stage
- `description` (string) - Description of new stage
- `tools_added` (array) - Tools added in new stage
- `tools_removed` (array) - Tools removed from previous stage
- `total_active_tools` (integer) - Total tools in new stage
- `active_tools` (array) - All tools in new stage

**Available Stages:**
- `setup` (8 tools) - Database initialization, collection creation, schema setup
- `data_loading` (6 tools) - Bulk data import, validation, initial indexing
- `analysis` (12 tools) - Query execution, graph traversal, statistics generation
- `cleanup` (5 tools) - Backup, validation, integrity checks, finalization

**Example:**
```json
{
  "stage": "data_loading"
}
```

**Result:**
```json
{
  "from_stage": "setup",
  "to_stage": "data_loading",
  "description": "Bulk data import, validation, initial indexing",
  "tools_added": [
    "arango_bulk_insert",
    "arango_bulk_update",
    "arango_insert_with_validation"
  ],
  "tools_removed": [
    "arango_create_collection",
    "arango_create_schema"
  ],
  "total_active_tools": 6,
  "active_tools": [
    "arango_bulk_insert",
    "arango_bulk_update",
    "arango_insert_with_validation",
    "arango_validate_references",
    "arango_create_index",
    "arango_list_indexes"
  ]
}
```

**Use Cases:**
- Structured data pipelines with clear stage boundaries
- Multi-phase workflows (setup → data_loading → analysis → cleanup)
- Automatic tool management for predictable patterns
- Reduce cognitive load during complex operations

**Best Practices:**
- Define clear stage boundaries in your workflow
- Advance stages when transitioning between major phases
- Let the server automatically manage tool loading/unloading
- Use for predictable, structured pipelines

---

#### arango_get_tool_usage_stats

Get usage statistics for all tools, including use counts and last used timestamps. Useful for understanding tool usage patterns and identifying unused tools.

**Parameters:**
- None (empty object or omitted)

**Returns:**
- `total_tools` (integer) - Total number of tools
- `tools_used` (integer) - Number of tools that have been used
- `tools_unused` (integer) - Number of tools never used
- `usage_stats` (array) - Per-tool statistics with name, use_count, last_used, category

**Example:**
```json
{}
```

**Result:**
```json
{
  "total_tools": 43,
  "tools_used": 12,
  "tools_unused": 31,
  "usage_stats": [
    {
      "name": "arango_query",
      "use_count": 45,
      "last_used": "2025-11-11T10:30:15Z",
      "category": "core_data"
    },
    {
      "name": "arango_create_graph",
      "use_count": 3,
      "last_used": "2025-11-11T09:15:42Z",
      "category": "graph_basic"
    },
    {
      "name": "arango_backup",
      "use_count": 0,
      "last_used": null,
      "category": "core_data"
    }
  ]
}
```

**Use Cases:**
- Identify unused tools to unload
- Analyze tool usage patterns for optimization
- Debug workflow issues by tracking tool invocations
- Generate usage reports for team visibility

**Best Practices:**
- Call periodically to monitor tool usage
- Unload tools with zero usage after initial setup
- Track usage patterns to optimize future workflows
- Use for workflow analysis and optimization

---

#### arango_unload_tools

Manually unload specific tools from the active context. Useful for fine-grained control over tool lifecycle.

**Parameters:**
- `tool_names` (array of strings, required) - List of tool names to unload from active context

**Returns:**
- `unloaded_tools` (array) - Tools successfully unloaded
- `not_found` (array) - Tools not found in active context
- `remaining_tools` (integer) - Number of tools still active
- `active_tools` (array) - All remaining active tools

**Example:**
```json
{
  "tool_names": ["arango_backup", "arango_create_schema", "arango_validate_document"]
}
```

**Result:**
```json
{
  "unloaded_tools": [
    "arango_backup",
    "arango_create_schema"
  ],
  "not_found": [
    "arango_validate_document"
  ],
  "remaining_tools": 8,
  "active_tools": [
    "arango_query",
    "arango_insert",
    "arango_update",
    "arango_remove",
    "arango_list_collections",
    "arango_create_collection",
    "arango_bulk_insert",
    "arango_bulk_update"
  ]
}
```

**Use Cases:**
- Remove tools after completing a specific task
- Clean up context before switching workflows
- Manually optimize tool set based on usage patterns
- Reduce cognitive load during complex operations

**Best Practices:**
- Unload tools immediately after completing tasks
- Don't unload tools you'll need again soon
- Combine with `arango_get_tool_usage_stats` to identify candidates
- Use for dynamic workflows where stages don't match your needs

---

## Toolset Configuration

Control available tools using the `MCP_COMPAT_TOOLSET` environment variable:

### Baseline Toolset

**Value:** `MCP_COMPAT_TOOLSET=baseline`

**Includes:** 7 core tools only
- arango_query
- arango_list_collections
- arango_insert
- arango_update
- arango_remove
- arango_create_collection
- arango_backup

**Use Cases:**
- Compatibility testing
- Minimal deployments
- Learning the basics

### Full Toolset (Default)

**Value:** `MCP_COMPAT_TOOLSET=full` (or unset)

**Includes:** All 43 tools across all categories

**Use Cases:**
- Production deployments
- Advanced graph operations
- MCP design pattern workflows
- Complete feature access

---

## Related Documentation
- [MCP Design Patterns Guide](./mcp-design-patterns.md) - Comprehensive guide to progressive discovery, context switching, and tool unloading
- [First Interaction Guide](../getting-started/first-interaction.md)
- [Graph Operations Guide](graph-operations.md)
- [Codebase Analysis Example](../examples/codebase-analysis.md)
- [Troubleshooting](troubleshooting.md)
