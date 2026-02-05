# mcp-arango-mind Architecture (v1.0)

**Design Philosophy**: Structure-oriented (aligned with ArangoDB native architecture)

---

## Core Principle

**Structure > Function**

Traditional approach groups by operation type (CRUD, admin, template).
Version 1.0 groups by ArangoDB structural layers (database, collection, view, graph).

This creates 1:1 mapping with official ArangoDB documentation and mental model.

---

## Tool Structure (5+1)

```
1. arango_database    ← Database-level operations
2. arango_collection  ← Collection-level operations (CRUD, index, schema)
3. arango_view        ← ArangoSearch view operations
4. arango_graph       ← Graph operations (traverse, backup)
5. arango_aql         ← Query-level operations (raw AQL + templates)
6. arango_mcp         ← Meta-management (unchanged)
```

**From previous architecture (46 tools) → v1.0 (5+1 tools)**

This consolidation reduces cognitive load while preserving all functionality:
- 46 discrete tools → 5 structure-aligned tools + 1 meta tool
- Function-oriented naming → Structure-oriented naming
- Better alignment with ArangoDB documentation

---

## Feature Integration from mcp-arangodb-async

### Core Features to Integrate

**Multi-Tenancy** (4 tools):
- Session-based database switching
- 6-level database resolution
- Multi-database connection pooling
- Per-tool database override

**Graph Management** (5 tools):
- Graph backup/restore with integrity validation
- Named graph batch backup
- Graph statistics and health checks

**Advanced Query** (4 tools):
- Query builder with filters/sorts
- Query profiling and performance analysis
- Query execution plan explanation
- Reference validation across collections

**Bulk Operations** (2 tools):
- Bulk insert with transaction support
- Bulk update with batch processing

**Schema Management** (2 tools):
- Schema creation and validation
- Document validation against schema

**Progressive Discovery** (6 tools):
- Tool search and categorization
- Workflow switching (beginner/expert modes)
- Tool usage statistics
- Dynamic tool loading/unloading

---

## Tool Specifications

### 1. arango_database

**Scope**: Multi-tenancy support - database switching and session context

**Operations (Implemented)**:
- `list` - List all configured databases
- `get_focused` - Get currently focused database for session
- `switch` - Switch focused database for session
- `get_resolution` - Show database resolution algorithm (6-level priority)

**Operations (Future - Move to CLI/arango_admin)**:
- `create` - Create new database (→ maa db create)
- `drop` - Drop database (→ maa db drop)
- `info` - Get database properties (→ included in list)

**Note**: Database/User creation/deletion are admin operations handled by CLI tools (`maa`), not MCP tools.

**Parameters**:
```
action: str (required)
  - "list": List configured databases
  - "get_focused": Get session's focused database
  - "switch": Set focused database
  - "get_resolution": Show resolution algorithm
database: str (optional, required for switch)
```

**Example**:
```json
{
  "action": "switch",
  "database": "proj_a_db"
}
```

---

### 2. arango_collection

**Scope**: Collection-level operations (CRUD + management)

**Operations**:

**CRUD (Fully Implemented)**:
- ✅ `insert` - Insert document
- ✅ `find` - Query documents (by key or with MongoDB-style filters: $gt, $gte, $lt, $lte, $ne, $in)
- ✅ `update` - Update document by _key
- ✅ `remove` - Remove document by _key
- ✅ `insert_with_validation` - Insert with cross-collection reference validation
- ✅ `list` - List all collections

**Batch Operations (Fully Implemented)**:
- ✅ `bulk_insert` - Bulk insert with transaction support
- ✅ `bulk_update` - Bulk update with batch processing
- ✅ `import` - Import from file with optional upsert (checks _key field)
- ✅ `export` - Export to file by key or filter with MongoDB-style operators

**Index Management (Fully Implemented)**:
- ✅ `create_index` - Create index (persistent, fulltext, geo, ttl)
- ✅ `list_indexes` - List all indexes
- ✅ `drop_index` - Drop index

**Schema Management (Fully Implemented)**:
- ✅ `create_schema` - Create/store JSON Schema validation
- ✅ `get_schema` - Retrieve stored schema for a collection
- ✅ `validate_document` - Validate document against schema (inline or stored)
- ✅ `validate_references` - Validate references across collections

**Stats (Partially Implemented)**:
- ✅ `stats` - Collection statistics (count, type, properties, figures)
- ❌ `recalc_weights` - Recalculate D-Heap weights **[TODO - mcp-arango-mind specific]**

**Management (Fully Implemented)**:
- ✅ `create` - Create collection (document/edge type)
- ✅ `drop` - Drop collection
- ✅ `truncate` - Truncate collection (remove all docs, keep structure)
- ✅ `stats` - Get collection statistics (count, type, properties)
- ✅ `list` - List all collections
- ✅ `backup` - Backup collection to file

**Parameters**:
```
action: str (required)
collection: str (required)

# CRUD fields
data: dict (for insert/update)
key: str (for find/update/remove)
filter: dict (for find)
limit: int (for find, default: 100)

# Import/Export
file_path: str
options: dict

# Index
index_type: str (persistent, fulltext, geo, ttl)
fields: list[str]
index_name: str

# Schema
schema: dict (JSON Schema Draft 7)
```

**Example**:
```json
{
  "action": "insert",
  "collection": "notes",
  "data": {
    "title": "ArangoDB Guide",
    "content": "...",
    "tags": ["database", "nosql", "graph"],
    "weight": 32
  }
}
```

---

### 3. arango_view

**Scope**: ArangoSearch view operations

**Operations (Fully Implemented)**:
- ✅ `create` - Create ArangoSearch view
- ✅ `drop` - Drop view
- ✅ `list` - List all views
- ✅ `get` - Get view properties
- ✅ `update` - Update view properties
- ✅ `search` - Execute search query against view

**Parameters**:
```
action: str (required)
name: str (view name)
type: str (default: "arangosearch")
properties: dict (view configuration)
query: str (for action=search)
```

**Example**:
```json
{
  "action": "create",
  "name": "notes_search",
  "type": "arangosearch",
  "properties": {
    "links": {
      "notes": {
        "fields": {
          "title": {"analyzers": ["text_en"]},
          "content": {"analyzers": ["text_en"]}
        }
      }
    }
  }
}
```

---

### 4. arango_graph

**Scope**: Named graph operations

**Operations**:

**Management**:
- `create` - Create graph with edge definitions
- `drop` - Drop graph
- `list` - List all graphs
- `get` - Get graph definition
- `add_vertex_collection` - Add vertex collection to graph
- `add_edge_definition` - Add edge definition to graph

**Vertex**:
- `add_vertex` - Add vertex to graph
- `remove_vertex` - Remove vertex

**Edge**:
- `add_edge` - Add edge (with _from/_to)
- `remove_edge` - Remove edge
- `list_edges` - List all edges

**Traversal** (from mcp-arangodb-async):
- `traverse` - Traverse graph (depth-first/breadth-first)
- `shortest_path` - Find shortest path between vertices
- `k_paths` - Find k shortest paths

**Backup & Restore** (from mcp-arangodb-async):
- `backup` - Backup single graph to file
- `restore` - Restore graph from file
- `backup_all` - Backup all named graphs
- `validate_integrity` - Validate graph structure integrity
- `statistics` - Get graph statistics (vertex/edge counts, depth)

**Parameters**:
```
action: str (required)
graph: str (graph name)

# Graph creation
edge_definitions: list[dict]
orphan_collections: list[str]

# Vertex/Edge ops
collection: str
data: dict
key: str
from_vertex: str (_id)
to_vertex: str (_id)

# Traversal
start_vertex: str (_id)
direction: str (outbound/inbound/any, default: outbound)
min_depth: int (default: 1)
max_depth: int (default: 3)

# Backup/Restore
file_path: str
```

**Example**:
```json
{
  "action": "traverse",
  "graph": "knowledge_graph",
  "start_vertex": "notes/123",
  "direction": "outbound",
  "max_depth": 2
}
```

---

### 5. arango_aql

**Scope**: AQL query execution

**Operations**:
- `query` - Execute raw AQL query
- `template` - Execute predefined template
- `explain` - Explain query execution plan
- `validate` - Validate AQL syntax

**Advanced Query Features** (from mcp-arangodb-async):
- `query_builder` - Build query from filters/sorts/pagination
- `query_profile` - Profile query performance with timing breakdown

**Parameters**:
```
action: str (default: "query")
query: str (AQL query string)
bind_vars: dict (bind variables)

# Template execution
template: str (template name, e.g., "memory.recent")
params: dict (template parameters)

# Query builder (action="query_builder")
collection: str
filters: list[dict] (e.g., [{"field": "weight", "operator": ">", "value": 50}])
sorts: list[dict] (e.g., [{"field": "created_at", "direction": "DESC"}])
limit: int
offset: int

# Query options
batch_size: int
ttl: int (seconds)
full_count: bool
profile: bool (enable profiling)
```

**Example**:
```json
{
  "action": "query",
  "query": "FOR doc IN notes FILTER doc.weight > @threshold RETURN doc",
  "bind_vars": {"threshold": 50}
}
```

**Template Example**:
```json
{
  "action": "template",
  "template": "memory.recent",
  "params": {"limit": 10}
}
```

---

### 6. arango_mcp

**Scope**: Meta-management and progressive discovery

**Core Operations** (from 0.5.x):
- `tools` - List all available tools
- `help` - Get help for specific tool
- `doc` - Get documentation
- `status` - Server status
- `version` - Server version

**Progressive Discovery** (from mcp-arangodb-async):
- `search_tools` - Search tools by keyword
- `list_by_category` - List tools grouped by category
- `tool_stats` - Get tool usage statistics

**Progressive Disclosure** (Three-Level Query Depth):
- **tools/list** - MCP native (auto-loaded by Claude)
- **arango_mcp: help** - Command format (on-demand)
- **arango_mcp: usage** - Full docs + examples (on-demand)

**Three-Level Architecture** (Query Depth, not Content Filtering):
```
Level 1: MCP tools/list (Always Loaded)
  → Returns: 6 tool names + short descriptions
  → ["arango_database: Database operations",
     "arango_collection: CRUD + batch + index + schema", ...]

Level 2: arango_mcp(action="help", tool="X") (On-Demand)
  → Returns: Command format for tool X
  → {action: "...", collection: "...", data: "...", filter: "..."}
  → Available operations list

Level 3: arango_mcp(action="usage", tool="X", operation="Y") (On-Demand)
  → Returns: Full documentation + examples
  → Format + examples + related operations + notes
```

**How It Works** (Zero Extra State):
```
1. Claude startup: MCP automatically calls tools/list
   → Sees 6 tools, knows names and general purpose

2. Claude needs detail: arango_mcp(action="help", tool="arango_collection")
   → Gets command format: {action, collection, data, key, filter, ...}
   → Knows what parameters are available

3. Claude needs example: arango_mcp(action="usage", tool="arango_collection", operation="bulk_insert")
   → Gets full example: {"action": "bulk_insert", "documents": [...]}
   → Knows exactly how to use it
```

**Why Query Depth > Mode/Workflow**:
```
Workflow/Mode:              Query Depth (1.0):
- Pre-filter operations     - No filtering (all operations available)
- Session state             - Zero state
- Switch commands           - Natural query when needed
- "Should I use this?"      - "Let me check usage"
```

---

## Multi-Tenancy Architecture (from mcp-arangodb-async)

### Design Overview

Multi-tenancy enables working with multiple databases in a single session without reconnecting.

**Key Components**:
1. **SessionState** - Per-session database context
2. **MultiDatabaseConnectionManager** - Connection pooling across databases
3. **Database Resolver** - 6-level resolution algorithm
4. **Per-Tool Override** - Every tool accepts `database` parameter

### Session State Management

```python
class SessionState:
    """Per-session state stored in MCP request context"""

    current_db: str = "_system"  # Active database name
    session_id: str  # Unique session identifier

    # Not stored in session (managed by connection manager):
    # - Database connections (pooled globally)
    # - Client instances (shared across sessions)
```

### 6-Level Database Resolution

Applied to every tool call in this order:

```
Priority 1: Explicit parameter
  → {"action": "insert", "collection": "notes", "database": "prod"}

Priority 2: Session state (set via arango_database switch)
  → session.current_db = "notes_prod"

Priority 3: Collection prefix parsing
  → collection="prod:notes" → database="prod", collection="notes"

Priority 4: YAML configuration file
  → config.yaml: default_database: "notes_dev"

Priority 5: Environment variable
  → ARANGO_DATABASE="test_db"

Priority 6: Hardcoded fallback
  → "_system"
```

### Multi-Database Connection Manager

```python
class MultiDatabaseConnectionManager:
    """Thread-safe multi-database connection pool

    Features:
    - Lazy connection initialization
    - Automatic retry on connection failure
    - Thread-safe connection reuse
    - Graceful cleanup on shutdown
    """

    def get_db(self, db_name: str, config: Config) -> StandardDatabase:
        """Get or create database connection (thread-safe)"""

    def close_db(self, db_name: str):
        """Close specific database connection"""

    def close_all(self):
        """Close all connections (called on shutdown)"""
```

### Integration Example

```python
# Tool handler receives db_name from resolver
def handle_insert(db_manager: MultiDatabaseConnectionManager,
                  session: SessionState,
                  args: dict):
    # Resolve database using 6-level algorithm
    db_name = resolve_database(
        explicit=args.get("database"),
        session_current=session.current_db,
        collection=args.get("collection"),
        config=load_config(),
    )

    # Get connection from pool
    db = db_manager.get_db(db_name, config)

    # Execute operation
    result = db.collection(args["collection"]).insert(args["document"])
    return result
```

---

## CLI Tools (from mcp-arangodb-async)

**Command**: `maa` (MCP ArangoDB Admin)

### Database Management (`maa db`)

```bash
maa db list                       # List all databases
maa db create <name>              # Create new database
maa db drop <name>                # Drop database
maa db switch <name>              # Switch active database (session)
maa db current                    # Show current database

# Configuration management
maa db add <name>                 # Add database config to YAML
maa db remove <name>              # Remove database config
maa db test <name>                # Test database connection
maa db status <name>              # Show database status
maa db update <name>              # Update database config
```

### User Management (`maa user`)

```bash
maa user list                     # List all users
maa user create <name>            # Create new user
maa user remove <name>            # Remove user
maa user grant <name> <db>        # Grant database access
maa user revoke <name> <db>       # Revoke database access
maa user databases <name>         # List user's databases
maa user password <name>          # Change user password
```

### Graph Operations (`maa graph`)

```bash
maa graph backup <name> <file>    # Backup single graph
maa graph restore <name> <file>   # Restore graph from backup
maa graph verify <file>           # Verify backup file integrity
```

### Health Check (`maa health`)

```bash
maa health check                  # Check server health
```

### Configuration File (`~/.maa/config.yaml`)

```yaml
# Multi-database configuration
databases:
  prod:
    url: http://localhost:8529
    username: root
    password: xxx
    database: notes_prod

  dev:
    url: http://localhost:8529
    username: root
    password: xxx
    database: notes_dev

default_database: dev
```

---

## Implementation Priority

### Phase 1: Core Operations (Week 1)
- `arango_database`: list, create, switch
- `arango_collection`: insert, find, update, remove
- `arango_aql`: query (raw)
- Basic multi-tenancy (SessionState + explicit database parameter)

### Phase 2: Advanced CRUD (Week 2)
- `arango_collection`: import, export, bulk_insert, bulk_update
- `arango_collection`: indexes (create, list, drop)
- `arango_collection`: schema (set, get, validate)
- `arango_aql`: template, explain

### Phase 3: Graph & Multi-Tenancy (Week 3)
- `arango_graph`: basic ops (create, list, add_vertex, add_edge, traverse)
- `arango_view`: basic ops (create, list, search)
- Full multi-tenancy (6-level resolution + MultiDatabaseConnectionManager)

### Phase 4: Progressive Disclosure & Advanced Graph (Week 4)
- **MCP native disclosure**: list (directory), help (format), usage (full docs)
- **Three-level structure**: L1/L2/L3 categorization in metadata
- `arango_graph`: backup, restore, validate_integrity, statistics
- `arango_mcp`: list, help, usage, search

### Phase 5: CLI & Optimization (Week 5-6)
- CLI tools (maa db/user/graph commands)
- Query builder & profiling
- Progressive tool loading/unloading
- Performance optimization

---

## Breaking Changes from 0.5.x

### Tool Renaming
- `arango_crud` → split into `arango_collection` (CRUD ops) + `arango_database` (management)
- `arango_admin` → split into structural tools
- `arango_template` → merged into `arango_aql` (action="template")
- `arango_optimize` → merged into `arango_collection` (stats, recalc_weights)

### Parameter Changes
- Collection CRUD now uses unified `action` parameter
- Database operations separated from collection operations
- Graph operations now require explicit `graph` parameter

### Migration Guide
```
0.5.x: arango_crud(op="insert", collection="notes", data={...})
1.0: arango_collection(action="insert", collection="notes", data={...})

0.5.x: arango_admin(action="create", target="collection", config={...})
1.0: arango_collection(action="create", collection="notes")

0.5.x: arango_template(name="memory.recent", params={...})
1.0: arango_aql(action="template", template="memory.recent", params={...})
```

---

## Design Benefits

### Mental Model Alignment
- Matches official ArangoDB documentation structure
- Intuitive for users familiar with ArangoDB
- Clear separation of concerns by layer

### Scalability
- Easy to add new operations within each layer
- Multi-tenancy support built-in
- Session state management for database switching

### Discoverability
- Tool names directly map to ArangoDB concepts
- Self-documenting structure
- IDE autocomplete friendly

---

## Success Metrics

- **User Experience**: Reduced time to first successful operation
- **Code Quality**: Pylint 10/10, 100% type coverage
- **Performance**: <100ms for simple queries, <500ms for complex traversals
- **Adoption**: 50% of mcp-arangodb-async users migrate within 3 months

---

**Status**: DRAFT
**Version**: 4.0.0-alpha
**Last Updated**: 2026-01-16
