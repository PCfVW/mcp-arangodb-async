# mcp-arangodb-async

ArangoDB MCP Server v4 -- AI Memory System with multi-tenancy, tag embedding, and graph optimization.

## Critical Rules

1. **Handler signature**: `handler(db: StandardDatabase, action: str, args: Dict[str, Any]) -> Dict[str, Any]`
   *WHY: entry.py extracts action before dispatch; all handlers follow this contract.*

2. **Return structured errors, log exceptions**: `logger.exception()` + `return {"error": ..., "available": [...]}`
   *WHY: MCP clients parse JSON; helpful errors reduce round-trips.*

3. **Validate collection existence before operations**: `db.has_collection(name)`
   *WHY: ArangoDB returns opaque errors for missing collections.*

4. **Type hint all function signatures**
   *WHY: Pydantic models rely on type metadata for schema generation.*

5. **Use JSON for all external APIs, reject CLI-style strings**
   *WHY: Type safety and MCP protocol consistency.*

## Architecture

```
mcp_arangodb_async/
  entry.py              # MCP server, tool registry (V4_TOOLS), lifespan
  http_transport.py     # HTTP/SSE transport alternative
  │
  ├── database/         # arango_database: multi-tenancy, session switching
  ├── collection/       # arango_collection: CRUD, batch, indexing, schema
  ├── view/             # arango_view: ArangoSearch view operations
  ├── graph/            # arango_graph: traversal, shortest_path, edge ops
  ├── admin/            # arango_admin: unified AQL + template + optimize
  │   ├── handler.py    #   routes 9 actions to sub-modules
  │   ├── models.py     #   AdminArgs (Pydantic)
  │   └── optimize/     #   unified optimize sub-module
  │       ├── handler.py    # dispatches sync/optimize/quality/embedding
  │       ├── sync.py       # sync_run: tags + tag_edges from notes.tags
  │       ├── edges.py      # optimize_run: access_logs behavior -> edge weights
  │       ├── quality.py    # quality_check: graph health metrics
  │       ├── embedding.py  # embedding_run: generate/search/status
  │       └── engine.py     # Qwen3-Embedding-0.6B, mean pooling, lazy-load
  ├── aql/              # AQL query/explain/profile/build (internal)
  ├── template/         # Template execution (internal)
  ├── mcp/              # arango_mcp: tool search, workflows, usage stats
  ├── utility/          # Shared: db, config, session, multi_db, resolver
  └── cli/              # CLI entry points

config/
  tools.json            # Tool metadata overlays
  help.json             # Help documentation
  admin.json            # Admin defaults (sync/optimize thresholds)
  workflows.json        # Workflow definitions
  schemas/              # JSON Schema Draft 7 per collection
  templates/            # AQL query templates by category
```

## V4 Tool Module Pattern

Each tool module follows this structure:

```
tool_name/
  __init__.py      # exports handler
  handler.py       # OPERATIONS dict + dispatch function
  models.py        # Pydantic BaseModel with action Literal
  operations_*.py  # Grouped operation functions
```

**Adding a new action**:
1. Write operation function in appropriate `.py` file
2. Register in `handler.py` OPERATIONS dict
3. Add action name to `models.py` Literal enum
4. No changes needed in `entry.py` (auto-discovered)

## MCP Tools (6 registered)

| Tool | Actions |
|------|---------|
| `arango_database` | list, get_focused, switch, get_resolution, list_available, backup, restore |
| `arango_collection` | insert, find, update, remove, list, bulk_insert, bulk_update, import, export, create, stats, drop, truncate, backup, + schema/index ops |
| `arango_view` | create, drop, list, get, update, search |
| `arango_graph` | create, list, add_vertex_collection, add_edge_definition, add_edge, traverse, shortest_path, backup, restore, validate_integrity, statistics |
| `arango_admin` | aql_query, aql_explain, aql_profile, aql_build, template_execute, sync_run, optimize_run, quality_check, embedding_run |
| `arango_mcp` | search_tools, list_by_category, get_workflow, list_workflows, usage_stats, unload |

## Key Technical Decisions

- **Embedding model**: Qwen3-Embedding-0.6B (1024 dim), only model with adequate Chinese embedding quality
- **Pooling**: Mean pooling over attention mask (CLS token produces indistinguishable vectors for short texts)
- **Vector search**: AQL `COSINE_SIMILARITY` brute-force, no vector index needed for ~2000 tags
- **Tag embedding storage**: `tags.embedding` field (List[float]), plus `embedding_text`, `embedding_model`, `embedded_at`
- **Multi-tenancy**: 6-level database resolution priority via `utility/resolver.py`
- **Transport**: stdio (default for Claude Desktop) or HTTP/SSE

## ArangoDB Schema

| Collection | Type | Key Fields |
|-----------|------|------------|
| `notes` | document | title, content, tags (array), weight, created_at |
| `tags` | document | label, count, aliases, embedding, embedding_model |
| `tag_edges` | edge | _from, _to, op (AND/OR/NOT/XOR), weight, confidence, enabled, source |
| `access_logs` | document | timestamp, target_ref, access_type |

## Commands

```bash
# Run MCP server (stdio)
.venv/bin/python -m mcp_arangodb_async.entry

# Run with HTTP transport
.venv/bin/python -m mcp_arangodb_async.cli.serve --transport http --port 8080

# Test imports
.venv/bin/python -c "from mcp_arangodb_async.entry import V4_TOOLS; print(list(V4_TOOLS.keys()))"
```

## Environment

- Python 3.11.2, python-arango 8.2.3
- torch 2.10.0+cpu, transformers 5.1.0 (for embedding engine)
- ArangoDB 3.12.4 at `http://192.168.10.32:8529` (user=claude, db=mindnext)
- Config: `ARANGO_DATABASES_CONFIG_FILE` or `config/databases.yaml`
