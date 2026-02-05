# mcp-arango-mind File Structure (v1.0)

**Design Principle**: One Tool = One Module, Operation Grouping = File Grouping

---

## Directory Overview

```
mcp-arangodb-async/
├── database/          # arango_database tool
├── collection/        # arango_collection tool
├── view/             # arango_view tool
├── graph/            # arango_graph tool
├── aql/              # arango_aql tool
├── mcp/              # arango_mcp tool
├── cli/              # maa command-line tools
├── utility/          # Shared utilities
├── entry.py          # MCP Server entry point
├── __init__.py
└── __main__.py
```

**Structure Levels**:
1. **Root directory** - 6 MCP tools + cli + utility + entry
2. **Tool directory** - handler + models + operation groups (as files)
3. **Operation group file** - related functions grouped together

---

## Tool Modules (6 Tools)

### 1. database/ - Database Operations

```
database/
├── __init__.py       # Module exports
├── handler.py        # Main entry point (dispatch)
└── models.py         # DatabaseArgs Pydantic model
```

**Operations**: list, create, drop, switch, info

**Rationale**: Only 5 operations, no need for sub-grouping

**handler.py structure**:
```python
def handle_database(db, args: DatabaseArgs):
    action = args.action

    if action == "list":
        return list_databases(db)
    elif action == "create":
        return create_database(db, args.name, args.users)
    elif action == "switch":
        return switch_database(db, args.name)
    # ...

def list_databases(db): ...
def create_database(db, name, users): ...
def drop_database(db, name): ...
def switch_database(db, name): ...
def info(db, name): ...
```

---

### 2. collection/ - Collection Operations

```
collection/
├── __init__.py       # Module exports
├── handler.py        # Main entry point (dispatch)
├── models.py         # CollectionArgs Pydantic model
├── crud.py           # CRUD operations (4 ops)
├── batch.py          # Batch operations (4 ops)
├── index.py          # Index management (3 ops)
├── schema.py         # Schema management (4 ops)
├── management.py     # Collection management (4 ops)
├── backup.py         # Backup/restore (2 ops)
└── stats.py          # Statistics (2 ops)
```

**Total**: 25+ operations grouped into 7 files

#### Operation Groups

| File | Operations | Description |
|------|-----------|-------------|
| `crud.py` | insert, find, update, remove | Basic CRUD |
| `batch.py` | bulk_insert, bulk_update, import, export | Batch operations |
| `index.py` | create_index, list_indexes, drop_index | Index management |
| `schema.py` | set_schema, get_schema, validate, validate_references | Schema validation |
| `management.py` | create, drop, list, truncate | Collection lifecycle |
| `backup.py` | backup, restore | Backup/restore |
| `stats.py` | stats, recalc_weights | Statistics & optimization |

#### handler.py structure

```python
from . import crud, batch, index, schema, management, backup, stats

OPERATIONS = {
    # CRUD
    "insert": crud.insert,
    "find": crud.find,
    "update": crud.update,
    "remove": crud.remove,

    # Batch
    "bulk_insert": batch.bulk_insert,
    "bulk_update": batch.bulk_update,
    "import": batch.import_file,
    "export": batch.export_file,

    # Index
    "create_index": index.create_index,
    "list_indexes": index.list_indexes,
    "drop_index": index.drop_index,

    # Schema
    "set_schema": schema.set_schema,
    "get_schema": schema.get_schema,
    "validate": schema.validate,
    "validate_references": schema.validate_references,

    # Management
    "create": management.create,
    "drop": management.drop,
    "list": management.list_collections,
    "truncate": management.truncate,

    # Backup
    "backup": backup.backup,
    "restore": backup.restore,

    # Stats
    "stats": stats.stats,
    "recalc_weights": stats.recalc_weights,
}

def handle_collection(db, args: CollectionArgs):
    operation = OPERATIONS.get(args.action)
    if not operation:
        return {"error": f"Unknown action: {args.action}"}
    return operation(db, args)
```

#### File Examples

**crud.py**:
```python
"""CRUD operations for arango_collection"""

def insert(db, args):
    """Insert document"""
    collection = db.collection(args.collection)
    return collection.insert(args.data)

def find(db, args):
    """Find documents with filter"""
    collection = db.collection(args.collection)
    cursor = collection.find(args.filter, limit=args.limit)
    return list(cursor)

def update(db, args):
    """Update document by key"""
    collection = db.collection(args.collection)
    return collection.update({"_key": args.key}, args.data)

def remove(db, args):
    """Remove document by key"""
    collection = db.collection(args.collection)
    return collection.delete(args.key)
```

**batch.py**:
```python
"""Batch operations for arango_collection"""

def bulk_insert(db, args):
    """Bulk insert documents"""
    collection = db.collection(args.collection)
    return collection.insert_many(args.documents)

def bulk_update(db, args):
    """Bulk update documents"""
    # Implementation...
    pass

def import_file(db, args):
    """Import from file"""
    # Implementation...
    pass

def export_file(db, args):
    """Export to file"""
    # Implementation...
    pass
```

---

### 3. view/ - ArangoSearch Operations

```
view/
├── __init__.py
├── handler.py
└── models.py
```

**Operations**: create, drop, list, get, update, search

**Rationale**: Only 6 operations, no need for sub-grouping

---

### 4. graph/ - Graph Operations

```
graph/
├── __init__.py
├── handler.py
├── models.py
├── management.py     # Graph lifecycle (4 ops)
├── vertex.py         # Vertex operations (3 ops)
├── edge.py           # Edge operations (3 ops)
├── traversal.py      # Traversal algorithms (3 ops)
├── backup.py         # Backup/restore (3 ops)
└── analysis.py       # Analysis & stats (2 ops)
```

**Total**: 18 operations grouped into 6 files

#### Operation Groups

| File | Operations | Description |
|------|-----------|-------------|
| `management.py` | create, drop, list, get | Graph lifecycle |
| `vertex.py` | add_vertex, remove_vertex, add_vertex_collection | Vertex operations |
| `edge.py` | add_edge, remove_edge, add_edge_definition | Edge operations |
| `traversal.py` | traverse, shortest_path, k_paths | Graph algorithms |
| `backup.py` | backup, restore, backup_all | Backup/restore |
| `analysis.py` | validate_integrity, statistics | Analysis |

---

### 5. aql/ - AQL Query Operations

```
aql/
├── __init__.py
├── handler.py
├── models.py
├── query.py          # Query execution (3 ops)
├── template.py       # Template system (2 ops)
└── builder.py        # Query building (2 ops)
```

**Total**: 7 operations grouped into 3 files

#### Operation Groups

| File | Operations | Description |
|------|-----------|-------------|
| `query.py` | query, explain, validate | Query execution |
| `template.py` | execute_template, list_templates | Template system |
| `builder.py` | query_builder, query_profile | Query construction |

---

### 6. mcp/ - Meta-Management

```
mcp/
├── __init__.py
├── handler.py
├── models.py
└── metadata.py       # Three-level query depth metadata
```

**Operations**: list, help, usage, search

**Rationale**: 4 operations for progressive disclosure (L1/L2/L3)

---

## Utility Module

```
utility/
├── __init__.py
├── config.py         # Configuration management
├── db.py             # Database connection
├── resolver.py       # 6-level database resolution
├── session.py        # Session state management
├── multi_db.py       # Multi-database connection pool
├── health.py         # Health check
└── converter.py      # Content converter
```

**Purpose**: Shared code across all tools

**Usage**:
```python
# In any tool handler
from utility.resolver import resolve_database
from utility.multi_db import get_db
from utility.session import get_session
```

---

## CLI Module

```
cli/
├── __init__.py
├── main.py           # CLI entry point
├── db.py             # maa db commands
├── user.py           # maa user commands
├── graph.py          # maa graph commands
└── health.py         # maa health commands
```

**Commands**:
- `maa db list|create|drop|switch|...`
- `maa user list|create|grant|...`
- `maa graph backup|restore|verify`
- `maa health check`

---

## Entry Point

```
entry.py              # MCP Server main entry
__init__.py           # Package initialization
__main__.py           # python -m mcp_arangodb_async
```

### entry.py Structure

```python
"""MCP Server entry point - unified tool dispatch"""

from mcp.server import Server

# Import tool handlers
from database import handle_database
from collection import handle_collection
from view import handle_view
from graph import handle_graph
from aql import handle_aql
from mcp import handle_mcp

# Tool registry
TOOLS = {
    "arango_database": handle_database,
    "arango_collection": handle_collection,
    "arango_view": handle_view,
    "arango_graph": handle_graph,
    "arango_aql": handle_aql,
    "arango_mcp": handle_mcp,
}

server = Server("mcp-arango-mind")

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Unified tool dispatch with common logic"""

    # Import shared utilities
    from utility import resolver, multi_db, session

    # Get handler
    handler = TOOLS.get(name)
    if not handler:
        return {"error": f"Unknown tool: {name}"}

    # Common preprocessing (all tools share this)
    session_obj = session.get_session()
    db_name = resolver.resolve_database(
        explicit=arguments.get("database"),
        session=session_obj.current_db,
        collection=arguments.get("collection"),
    )
    db = multi_db.get_db(db_name)

    # Dispatch to specific tool handler
    return handler(db, arguments)
```

---

## Design Principles

### 1. One Tool = One Module

```
Tool name          Directory
─────────────────  ─────────
arango_database    database/
arango_collection  collection/
arango_view        view/
arango_graph       graph/
arango_aql         aql/
arango_mcp         mcp/
```

### 2. Operation Grouping = File Grouping

```
Documentation Group    Code File
─────────────────────  ─────────────
CRUD                   crud.py
Batch                  batch.py
Index Management       index.py
Schema Management      schema.py
```

**1:1 mapping between docs and code**

### 3. Shared Code in utility/

```
All common logic:
- Database resolution
- Connection pooling
- Session management
- Configuration
→ Lives in utility/
```

### 4. Unified Entry Point

```
entry.py handles:
- Tool registry
- Common preprocessing
- Dispatch to handlers
```

---

## File Naming Conventions

### Module Files
- `handler.py` - Main entry point for the tool
- `models.py` - Pydantic models for the tool
- `{group}.py` - Operation group (e.g., `crud.py`, `batch.py`)

### Function Naming
- Operation functions: lowercase with underscores (e.g., `bulk_insert()`)
- Handler functions: `handle_{tool}()` (e.g., `handle_collection()`)

### Import Convention
```python
# Absolute imports for cross-module
from utility.resolver import resolve_database

# Relative imports within module
from . import crud, batch, index
```

---

## Testing Structure

```
tests/
├── database/
│   └── test_handler.py
├── collection/
│   ├── test_crud.py
│   ├── test_batch.py
│   ├── test_index.py
│   ├── test_schema.py
│   ├── test_management.py
│   ├── test_backup.py
│   └── test_stats.py
├── view/
│   └── test_handler.py
├── graph/
│   ├── test_management.py
│   ├── test_vertex.py
│   ├── test_edge.py
│   ├── test_traversal.py
│   ├── test_backup.py
│   └── test_analysis.py
├── aql/
│   ├── test_query.py
│   ├── test_template.py
│   └── test_builder.py
├── mcp/
│   └── test_handler.py
└── utility/
    ├── test_resolver.py
    ├── test_session.py
    └── test_multi_db.py
```

**Testing matches code structure 1:1**

---

## Migration from mcp-arangodb-async

### File Movement Plan

**Phase 1: Core utilities**
```bash
# Move to utility/
config.py → utility/config.py
db.py → utility/db.py
session_state.py → utility/session.py
multi_db_manager.py → utility/multi_db.py
db_resolver.py → utility/resolver.py
health.py → utility/health.py
content_converter.py → utility/converter.py
```

**Phase 2: Tool handlers**
```bash
# Create new structure
handlers.py (46 tools) → split into:
  - database/handler.py
  - collection/{handler.py, crud.py, batch.py, ...}
  - view/handler.py
  - graph/{handler.py, management.py, vertex.py, ...}
  - aql/{handler.py, query.py, template.py, ...}
  - mcp/handler.py
```

**Phase 3: CLI**
```bash
# Move to cli/
cli_db.py → cli/db.py
cli_user.py → cli/user.py
cli_health.py → cli/health.py
# Add cli/graph.py (new)
```

---

## Summary Statistics

**File Count**:
- Database: 3 files
- Collection: 10 files (handler + models + 7 groups)
- View: 3 files
- Graph: 8 files (handler + models + 6 groups)
- AQL: 6 files (handler + models + 3 groups)
- MCP: 4 files (handler + models + metadata)
- CLI: 5 files
- Utility: 9 files
- Entry: 3 files

**Total**: ~51 files

**Code Reduction**:
- From 46 discrete tool files
- To 6 modular tool directories
- 80% code reuse through utility/

---

**Version**: 1.0.0
**Status**: Released
**Last Updated**: 2026-01-17
