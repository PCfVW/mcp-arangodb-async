# ArangoDB MCP Server for Python - Enhanced Edition

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/Protocol-MCP-%23555555)](https://modelcontextprotocol.io/)
[![Graph Tools](https://img.shields.io/badge/Graph_Tools-Enhanced-orange)](https://docs.arangodb.com/stable/graphs/)

A comprehensive, production-ready MCP stdio server exposing advanced ArangoDB operations to MCP clients (Claude Desktop, Augment Code). Features async-first Python architecture, wrapping the official `python-arango` driver with graph management capabilities, flexiblecontent conversion utilities (JSON, Markdown, YAML and Table), comprehensive backup/restore functionality, and analytics capabilities.
---

## Architecture at a Glance

Your AI Assistant interacts with this enhanced server, which provides both basic and advanced ArangoDB operations.

```
+------------------------+      +-------------------------+      +----------------------+
|   MCP Client           |      |   ArangoDB MCP Server   |      |   ArangoDB           |
| (Claude, Augment, etc.)|----->|   (Enhanced Python)     |----->|   (Docker Container) |
|                        |      |   • Core Tools          |      |   • Multi-Model DB   |
|                        |      |   • Graph Management    |      |   • Graph Engine     |
|                        |      |   • Content Conversion  |      |   • AQL Engine       |
+------------------------+      +-------------------------+      +----------------------+
```

## Table of Contents
- [Architecture at a Glance](#architecture-at-a-glance)
- [Why Run ArangoDB in Docker?](#why-run-arangodb-in-docker)
- [Quick Start (Windows)](#quick-start-windows)
- [First Successful Interaction](#first-successful-interaction)
- [Exposed MCP Tools](#exposed-mcp-tools)
- [Direct Python Function Usage](#direct-python-function-usage)
- [Enhanced Use Case Example: Codebase Graph Analysis](#enhanced-use-case-example-codebase-graph-analysis)
- [Running Tests](#running-tests)
- [Not Implemented (by Design)](#not-implemented-by-design)
- [Troubleshooting (PowerShell)](#troubleshooting-powershell)
- [Appendix A: License Notes (ArangoDB)](#appendix-a-license-notes-arangodb)
- [Appendix B: Python File Index](#appendix-b-python-file-index)
- [References](#references)

---

## Why Run ArangoDB in Docker?
- **Stability and isolation**: Avoid host conflicts and "works on my machine" issues
- **Zero-install DB**: Start/stop with `docker compose`
- **Reproducibility**: Same image/tag across teammates and CI
- **Health checks baked-in**: Readiness validation in compose
- **Fast reset**: Recreate clean instances easily
- **Portability**: Consistent on Windows/macOS/Linux

### Persistent Data Configuration (Recommended)

Edit your `docker-compose.yml` to preserve data across container restarts:

```yaml
services:
  arangodb:
    image: arangodb:3.11
    container_name: mcp_arangodb_test
    environment:
      ARANGO_ROOT_PASSWORD: ${ARANGO_ROOT_PASSWORD:-changeme}
    ports:
      - "8529:8529"
    healthcheck:
      test: arangosh --server.username root --server.password "$ARANGO_ROOT_PASSWORD" --javascript.execute-string "require('@arangodb').db._version()" > /dev/null 2>&1 || exit 1
      interval: 5s
      timeout: 2s
      retries: 30
    restart: unless-stopped
    volumes:
      - arango_data:/var/lib/arangodb3

volumes:
  arango_data:
```

---

## Quick Start (Windows)

### Prerequisites
- Docker Desktop (for ArangoDB)
- Python 3.11+

### Installation Steps

1) **Clone and install dependencies**
```powershell
git clone https://github.com/ravenwits/mcp-server-arangodb-python.git
cd "mcp-server-arangodb-python"
python -m pip install -r requirements.txt
```

2) **Start ArangoDB (via Docker)**
```powershell
# In repo root
docker compose up -d
```

3) **Initialize database and user**
```powershell
# Creates database mcp_arangodb_test and user mcp_arangodb_user/mcp_arangodb_password
scripts\setup-arango.ps1 -RootPassword "changeme" -DbName "mcp_arangodb_test" -User "mcp_arangodb_user" -Password "mcp_arangodb_password" -Seed
```

4) **Configure environment (.env recommended)**
```powershell
# Create local .env from template
Copy-Item env.example .env
notepad .env
```

Example .env contents:
```dotenv
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
ARANGO_TIMEOUT_SEC=30.0
```

5) **Verify installation**
```powershell
python -m mcp_arangodb_async --health
```

Expected JSON: `{"ok": true, "db": "mcp_arangodb_test", "user": "mcp_arangodb_user"}`

6) **Run the MCP server**
```powershell
python -m mcp_arangodb_async
```

---

## First Successful Interaction

### Claude Desktop Configuration
Add this server entry to your Claude MCP config:

```json
{
  "mcpServers": {
    "arangodb": {
      "command": "python",
      "args": ["-m", "mcp_arangodb_async"],
      "env": {
        "ARANGO_URL": "http://localhost:8529",
        "ARANGO_DB": "mcp_arangodb_test",
        "ARANGO_USERNAME": "mcp_arangodb_user",
        "ARANGO_PASSWORD": "mcp_arangodb_password"
      }
    }
  }
}
```

### Augment Code Configuration
**Settings UI Option:**
- Server name: "ArangoDB"
- Command: `mcp-arangodb-async` (console script) or `python`
- Args: `["-m", "mcp_arangodb_async.entry"]`
- Environment variables: Same as above

**Import JSON Option:**
```json
{
  "mcpServers": {
    "arangodb": {
      "command": "mcp-arangodb-async",
      "env": {
        "ARANGO_URL": "http://localhost:8529",
        "ARANGO_DB": "mcp_arangodb_test",
        "ARANGO_USERNAME": "mcp_arangodb_user",
        "ARANGO_PASSWORD": "mcp_arangodb_password"
      }
    }
  }
}
```

### First Test Prompts
1. **Basic functionality**: "List all collections in my database."
2. **Write test**: "Use arango_insert to add {'name': 'test_document', 'value': 1} to a collection named 'tests'."
3. **Graph test**: "Create a simple graph with users and follows relationships, then traverse from a specific user."

---

## Exposed MCP Tools

The server provides 33 comprehensive tools organized into logical categories. Each tool uses strict Pydantic validation and consistent error handling.

### Core Data Operations (7)
- **arango_query** — Execute AQL with optional bind vars; returns rows
- **arango_list_collections** — List non-system collections
- **arango_insert** — Insert a document into a collection
- **arango_update** — Update a document by key in a collection
- **arango_remove** — Remove a document by key from a collection
- **arango_create_collection** — Create a collection (document or edge) or return properties
- **arango_backup** — Backup collections to JSON files

### Indexing & Query Analysis (4)
- **arango_list_indexes** — List indexes for a collection
- **arango_create_index** — Create index (persistent, hash, skiplist, ttl, fulltext, geo)
- **arango_delete_index** — Delete index by id or name
- **arango_explain_query** — Explain AQL and return plans/warnings/stats

### Validation & Bulk Operations (4)
- **arango_validate_references** — Validate that reference fields point to existing docs
- **arango_insert_with_validation** — Insert after reference validation
- **arango_bulk_insert** — Batch insert with error accounting
- **arango_bulk_update** — Batch update by key

### Schema Management (2)
- **arango_create_schema** — Create or update a named JSON Schema
- **arango_validate_document** — Validate a document against stored or inline schema

### Enhanced Query Tools (2)
- **arango_query_builder** — Build simple AQL with filters/sort/limit
- **arango_query_profile** — Explain a query and return plans/stats for profiling

### Basic Graph Operations (7)
- **arango_create_graph** — Create a named graph with edge definitions
- **arango_add_edge** — Insert an edge between vertices with optional attributes
- **arango_traverse** — Traverse a graph from a start vertex with depth bounds
- **arango_shortest_path** — Compute shortest path between two vertices
- **arango_list_graphs** — List graphs in the database
- **arango_add_vertex_collection** — Add a vertex collection to a graph
- **arango_add_edge_definition** — Create an edge definition for a graph

### Advanced Graph Management Tools (5)
- **arango_backup_graph** — Export complete graph structure including vertices, edges, and metadata.
- **arango_restore_graph** — Import graph data with referential integrity validation and conflict resolution.
- **arango_backup_named_graphs** — Backup graph definitions from _graphs system collection.
- **arango_validate_graph_integrity** — Validate graph consistency and find orphaned edges.
- **arango_graph_statistics** — Generate comprehensive graph analytics including vertex/edge counts, degree distribution, and connectivity metrics.

### **Advanced Graph Management Tools: Details**

#### **arango_backup_graph**
Export complete graph structure including vertices, edges, and metadata.

**Parameters:**
- `graph_name` (required): Name of the graph to backup
- `output_dir` (optional): Directory for backup files (auto-generated if not provided)
- `include_metadata` (optional, default: true): Include graph metadata and structure
- `doc_limit` (optional): Limit documents per collection for large graphs

**Returns:**
```json
{
  "graph_name": "social_network",
  "output_dir": "/tmp/backup_20240101_120000",
  "vertex_files": [{"collection": "users", "count": 1000, "file": "vertices/users.json"}],
  "edge_files": [{"collection": "follows", "count": 2500, "file": "edges/follows.json"}],
  "total_vertex_collections": 1,
  "total_edge_collections": 1,
  "total_documents": 3500,
  "metadata_included": true
}
```

**Usage Example:**
```
Use arango_backup_graph to export my 'social_network' graph to '/tmp/social_backup' including all metadata.
```

#### **arango_restore_graph**
Import graph data with referential integrity validation and conflict resolution.

**Parameters:**
- `input_dir` (required): Directory containing graph backup files
- `graph_name` (optional): Name for restored graph (uses original if not provided)
- `conflict_resolution` (optional, default: "error"): How to handle conflicts ("skip", "overwrite", "error")
- `validate_integrity` (optional, default: true): Validate referential integrity during restore

**Returns:**
```json
{
  "graph_name": "restored_social_network",
  "original_graph_name": "social_network",
  "input_dir": "/tmp/social_backup",
  "restored_vertices": [{"collection": "users", "inserted": 950, "updated": 50}],
  "restored_edges": [{"collection": "follows", "inserted": 2400, "updated": 100}],
  "graph_created": true,
  "conflicts": [],
  "errors": [],
  "integrity_report": {"valid": true, "orphaned_edges": 0},
  "total_documents_restored": 3500
}
```

#### **arango_backup_named_graphs**
Backup graph definitions from _graphs system collection.

**Parameters:**
- `output_file` (optional): Output JSON file path (auto-generated if not provided)
- `graph_names` (optional): Specific graphs to backup (all if not provided)

**Returns:**
```json
{
  "output_file": "/tmp/graph_definitions.json",
  "graphs_backed_up": 3,
  "missing_graphs": [],
  "backup_size_bytes": 2048
}
```

#### **arango_validate_graph_integrity**
Verify graph consistency, orphaned edges, and constraint violations.

**Parameters:**
- `graph_name` (optional): Specific graph to validate (all if not provided)
- `check_orphaned_edges` (optional, default: true): Check for edges with missing vertices
- `check_constraints` (optional, default: true): Validate graph constraints
- `return_details` (optional, default: false): Return detailed violation information

**Returns:**
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

#### **arango_graph_statistics**
Generate comprehensive graph analytics including vertex/edge counts, degree distribution, and connectivity metrics.

**Parameters:**
- `graph_name` (optional): Specific graph to analyze (all if not provided)
- `include_degree_distribution` (optional, default: true): Calculate degree distribution
- `include_connectivity` (optional, default: true): Calculate connectivity metrics
- `sample_size` (optional, minimum: 100): Sample size for connectivity analysis

**Returns:**
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

### Tool Aliases (2)
- **arango_graph_traversal** — Alias for arango_traverse
- **arango_add_vertex** — Alias for arango_insert (clarity in graph workflows)

### Toolset Configuration
Control available tools using `MCP_COMPAT_TOOLSET` environment variable:
- `baseline` — Core 7 tools only (for compatibility testing)
- `full` — All 33 tools including advanced graph management (default)

---

## Direct Python Function Usage

The server provides direct access to all functionality through Python functions, allowing flexible usage patterns beyond the MCP protocol.

### Quickstart Guide

All handler functions follow the pattern: `(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]`

```python
from mcp_arangodb_async.db import get_client_and_db
from mcp_arangodb_async.config import load_config
from mcp_arangodb_async.handlers import (
    handle_backup_graph,
    handle_graph_statistics,
    handle_validate_graph_integrity
)

# Setup database connection
config = load_config()
client, db = get_client_and_db(config)

# Example 1: Backup a graph
backup_result = handle_backup_graph(db, {
    "graph_name": "social_network",
    "output_dir": "/tmp/backup",
    "include_metadata": True
})

print(f"Backed up {backup_result['total_documents']} documents to {backup_result['output_dir']}")

# Example 2: Analyze graph statistics
stats_result = handle_graph_statistics(db, {
    "graph_name": "social_network",
    "include_degree_distribution": True,
    "sample_size": 200
})

for graph_stat in stats_result["statistics"]:
    print(f"Graph: {graph_stat['graph_name']}")
    print(f"Vertices: {graph_stat['total_vertices']}")
    print(f"Edges: {graph_stat['total_edges']}")
    print(f"Density: {graph_stat['density']:.4f}")
```

### MCPContentConverter Class

Transform handler results into multiple output formats for enhanced readability and integration.

```python
from mcp_arangodb_async.content_converter import (
    MCPContentConverter,
    DEFAULT_CONVERTER,
    PRETTY_CONVERTER,
    MARKDOWN_CONVERTER,
    create_converter
)

# Example: Convert graph statistics to different formats
stats_result = handle_graph_statistics(db, {"graph_name": "social_network"})

# Option 1: Use pre-configured converters
json_content = DEFAULT_CONVERTER.to_text_content(stats_result, format_style="json")
markdown_content = MARKDOWN_CONVERTER.to_text_content(
    stats_result, 
    format_style="markdown",
    title="Graph Analytics Report"
)

# Option 2: Create custom converter
custom_converter = create_converter(pretty=True, include_timestamps=True)
yaml_content = custom_converter.to_text_content(stats_result, format_style="yaml")

# Option 3: Mixed content (human-readable + structured)
text_content, structured_data = MARKDOWN_CONVERTER.to_mixed_content(
    stats_result,
    summary="Graph analysis completed successfully with detailed metrics.",
    title="Social Network Analysis"
)

# Access the results
print(json_content[0].text)  # JSON string
print(markdown_content[0].text)  # Formatted Markdown
print(structured_data["graphs_analyzed"])  # Direct dict access
```

### Available Output Formats

1. **JSON** (default): Compact or pretty-printed JSON
2. **Markdown**: Structured Markdown with tables and sections
3. **YAML**: Human-readable YAML format (requires PyYAML)
4. **Table**: ASCII tables for list data (requires tabulate)

### Pre-configured Converters

- **DEFAULT_CONVERTER**: Compact JSON output
- **PRETTY_CONVERTER**: Indented JSON with sorted keys
- **MARKDOWN_CONVERTER**: Markdown format with timestamps
- **COMPACT_CONVERTER**: ASCII-safe compact format

---

## Enhanced Use Case Example: Codebase Graph Analysis

This comprehensive example demonstrates building a sophisticated graph database representing this MCP server project's codebase structure, showcasing advanced ArangoDB capabilities and the new graph management tools.

### Graph Model Design

**Vertex Collections:**
- **folders** — Directory nodes with metadata (path, type, size)
- **files** — Python file nodes with metrics (lines, complexity, imports)
- **functions** — Function definitions with signatures and complexity
- **classes** — Class definitions with methods and inheritance
- **modules** — Import modules with dependency information

**Edge Collections:**
- **contains** — Folder→File, Folder→Subfolder relationships
- **defines** — File→Function, File→Class relationships  
- **imports** — File→Module dependency relationships
- **calls** — Function→Function call relationships
- **inherits** — Class→Class inheritance relationships

### Implementation Example

```python
# Step 1: Create the codebase analysis graph
create_graph_result = await call_tool("arango_create_graph", {
    "name": "codebase_analysis",
    "edge_definitions": [
        {
            "collection": "contains",
            "from": ["folders"],
            "to": ["folders", "files"]
        },
        {
            "collection": "defines", 
            "from": ["files"],
            "to": ["functions", "classes"]
        },
        {
            "collection": "imports",
            "from": ["files"],
            "to": ["modules"]
        },
        {
            "collection": "calls",
            "from": ["functions"],
            "to": ["functions"]
        }
    ]
})

# Step 2: Populate with codebase data
folders_data = [
    {"_key": "root", "path": ".", "type": "root", "file_count": 15},
    {"_key": "mcp_arangodb", "path": "mcp_arangodb", "type": "package", "file_count": 10},
    {"_key": "tests", "path": "tests", "type": "test_package", "file_count": 12}
]

files_data = [
    {"_key": "entry_py", "path": "mcp_arangodb/entry.py", "lines": 600, "complexity": 15, "functions": 8},
    {"_key": "handlers_py", "path": "mcp_arangodb/handlers.py", "lines": 1300, "complexity": 25, "functions": 29},
    {"_key": "models_py", "path": "mcp_arangodb/models.py", "lines": 800, "complexity": 10, "classes": 25},
    {"_key": "graph_backup_py", "path": "mcp_arangodb/graph_backup.py", "lines": 650, "complexity": 20, "functions": 6}
]

functions_data = [
    {"_key": "handle_backup_graph", "name": "handle_backup_graph", "file": "handlers_py", "complexity": 3, "params": 2},
    {"_key": "backup_graph_to_dir", "name": "backup_graph_to_dir", "file": "graph_backup_py", "complexity": 8, "params": 4},
    {"_key": "validate_graph_integrity", "name": "validate_graph_integrity", "file": "graph_backup_py", "complexity": 12, "params": 4}
]

# Bulk insert all data
await call_tool("arango_bulk_insert", {"collection": "folders", "documents": folders_data})
await call_tool("arango_bulk_insert", {"collection": "files", "documents": files_data})
await call_tool("arango_bulk_insert", {"collection": "functions", "documents": functions_data})

# Step 3: Create relationships
contains_edges = [
    {"_from": "folders/root", "_to": "folders/mcp_arangodb", "relationship": "contains"},
    {"_from": "folders/mcp_arangodb", "_to": "files/entry_py", "relationship": "contains"},
    {"_from": "folders/mcp_arangodb", "_to": "files/handlers_py", "relationship": "contains"}
]

defines_edges = [
    {"_from": "files/handlers_py", "_to": "functions/handle_backup_graph", "relationship": "defines"},
    {"_from": "files/graph_backup_py", "_to": "functions/backup_graph_to_dir", "relationship": "defines"}
]

calls_edges = [
    {"_from": "functions/handle_backup_graph", "_to": "functions/backup_graph_to_dir", "relationship": "calls", "call_type": "direct"}
]

await call_tool("arango_bulk_insert", {"collection": "contains", "documents": contains_edges})
await call_tool("arango_bulk_insert", {"collection": "defines", "documents": defines_edges})
await call_tool("arango_bulk_insert", {"collection": "calls", "documents": calls_edges})
```

### Advanced Graph Analysis Examples

#### 1. Function Call Chain Analysis
```python
# Simulate function calling chains using graph traversal
call_chain_query = """
FOR vertex, edge, path IN 1..5 OUTBOUND 'functions/handle_backup_graph'
GRAPH 'codebase_analysis'
FILTER edge.relationship == 'calls'
RETURN {
    function: vertex.name,
    depth: LENGTH(path.edges),
    call_path: path.edges[*].call_type,
    complexity: vertex.complexity
}
"""

call_chains = await call_tool("arango_query", {
    "query": call_chain_query
})
```

#### 2. Dependency Analysis
```python
# Find files with highest import dependencies
dependency_analysis = """
FOR file IN files
LET import_count = LENGTH(
    FOR v, e IN 1..1 OUTBOUND file._id
    GRAPH 'codebase_analysis'
    FILTER e.relationship == 'imports'
    RETURN v
)
LET complexity_score = file.complexity + (import_count * 0.5)
SORT complexity_score DESC
LIMIT 10
RETURN {
    file: file.path,
    lines: file.lines,
    complexity: file.complexity,
    import_dependencies: import_count,
    complexity_score: complexity_score
}
"""

complexity_analysis = await call_tool("arango_query", {
    "query": dependency_analysis
})
```

#### 3. Graph Statistics for Code Metrics
```python
# Use the new graph statistics tool to analyze codebase structure
codebase_stats = await call_tool("arango_graph_statistics", {
    "graph_name": "codebase_analysis",
    "include_degree_distribution": true,
    "include_connectivity": true,
    "sample_size": 100
})

# Interpret results for code quality metrics
stats = codebase_stats["statistics"][0]
print(f"Codebase Complexity Metrics:")
print(f"- Total Components: {stats['total_vertices']}")
print(f"- Total Relationships: {stats['total_edges']}")
print(f"- Interconnectedness (Density): {stats['density']:.4f}")
print(f"- Average Dependencies per Component: {stats['avg_out_degree']:.2f}")
print(f"- Maximum Component Dependencies: {stats['max_out_degree']}")
```

#### 4. Module Interconnectedness Analysis
```python
# Find most interconnected modules using centrality analysis
centrality_query = """
FOR file IN files
LET in_degree = LENGTH(
    FOR v, e IN 1..1 INBOUND file._id
    GRAPH 'codebase_analysis'
    RETURN v
)
LET out_degree = LENGTH(
    FOR v, e IN 1..1 OUTBOUND file._id  
    GRAPH 'codebase_analysis'
    RETURN v
)
LET centrality = in_degree + out_degree
SORT centrality DESC
LIMIT 5
RETURN {
    module: file.path,
    in_degree: in_degree,
    out_degree: out_degree,
    centrality: centrality,
    complexity: file.complexity
}
"""

centrality_analysis = await call_tool("arango_query", {
    "query": centrality_query
})
```

### Creative Graph Modeling Techniques

#### 1. Temporal Code Evolution Graph
```python
# Model code changes over time with temporal edges
temporal_edges = [
    {
        "_from": "functions/handle_backup_graph_v1",
        "_to": "functions/handle_backup_graph_v2", 
        "relationship": "evolves_to",
        "timestamp": "2024-01-15T10:00:00",
        "change_type": "enhancement",
        "lines_changed": 25
    }
]
```

#### 2. Complexity Hotspot Detection
```python
# Use graph traversal to find complexity hotspots
hotspot_query = """
FOR file IN files
FILTER file.complexity > 15
LET dependent_files = (
    FOR v, e, p IN 1..3 INBOUND file._id
    GRAPH 'codebase_analysis'
    FILTER e.relationship IN ['imports', 'calls']
    RETURN DISTINCT v.path
)
RETURN {
    hotspot: file.path,
    complexity: file.complexity,
    impact_radius: LENGTH(dependent_files),
    affected_files: dependent_files
}
"""
```

#### 3. Refactoring Impact Analysis
```python
# Simulate refactoring impact using graph algorithms
impact_analysis = """
FOR start_file IN files
FILTER start_file.path == 'mcp_arangodb/handlers.py'
FOR vertex, edge, path IN 1..10 OUTBOUND start_file._id
GRAPH 'codebase_analysis'
COLLECT impact_level = LENGTH(path.edges) WITH COUNT INTO affected_count
RETURN {
    refactoring_file: start_file.path,
    impact_level: impact_level,
    affected_components: affected_count
}
"""
```

### Graph Backup and Restore Workflow

```python
# Complete workflow: backup, analyze, restore
# 1. Backup the codebase graph
backup_result = await call_tool("arango_backup_graph", {
    "graph_name": "codebase_analysis",
    "output_dir": "/tmp/codebase_backup",
    "include_metadata": true
})

# 2. Validate integrity before analysis
integrity_result = await call_tool("arango_validate_graph_integrity", {
    "graph_name": "codebase_analysis",
    "return_details": true
})

# 3. Generate comprehensive statistics
stats_result = await call_tool("arango_graph_statistics", {
    "graph_name": "codebase_analysis",
    "include_degree_distribution": true,
    "include_connectivity": true
})

# 4. Restore to test environment for experimentation
restore_result = await call_tool("arango_restore_graph", {
    "input_dir": "/tmp/codebase_backup",
    "graph_name": "codebase_test",
    "conflict_resolution": "overwrite"
})
```

### Traditional Use Cases (Maintained)

**Claude Desktop Examples:**
- **Music**: "Build a piano‑jazz knowledge graph of Artists, Albums, Sub‑genres, and Influence edges. Create indexes, then traverse to curate a 10‑track lineage playlist starting from 'Michel Petrucciani'."
- **Space**: "Model missions, spacecraft, instruments, targets (Mars, Europa…) as vertices and 'observed_with' edges. Find shortest paths from 'ion propulsion' to 'first detection of water ice'."
- **Travel**: "Create a city graph with flight edges (cost, CO2, duration). Compute a route minimizing total CO2 under a 10-day constraint."

**Augment Code Examples:**
- **Schema Design**: "Design JSON Schemas for 'User' and 'Session', migrate existing documents, and generate validation flows."
- **Performance**: "Profile slow AQL in 'orders' and propose indexes; create those indexes and re-profile to confirm improvement."
- **Testing**: "Generate seed data for integration tests, bulk insert it, and provide cleanup steps."

---

## Running Tests

The project includes a comprehensive test suite covering unit tests, integration tests, and graph management functionality.

### Prerequisites for Testing

```powershell
# Install development dependencies
python -m pip install -r requirements-dev.txt

# Ensure ArangoDB is running for integration tests
docker compose up -d arangodb
```

### Test Categories

#### 1. Unit Tests
Test individual components in isolation with mocked dependencies.

```powershell
# Run all unit tests
python -m pytest tests/ -k "unit" -v

# Run specific component tests
python -m pytest tests/test_models_unit.py -v
python -m pytest tests/test_handlers_unit.py -v
python -m pytest tests/test_graph_backup_unit.py -v
python -m pytest tests/test_content_converter.py -v
```

#### 2. Integration Tests
Test MCP protocol functionality and database interactions.

```powershell
# Run all integration tests
python -m pytest tests/test_mcp_integration.py -v
python -m pytest tests/test_graph_integration.py -v

# Run with specific toolset
MCP_COMPAT_TOOLSET=full python -m pytest tests/test_mcp_integration.py::TestMCPIntegration::test_list_tools_full_set -v
```

#### 3. Graph Management Tests
Test the new graph backup, restore, and analytics functionality.

```powershell
# Run graph-specific tests
python -m pytest tests/ -k "graph" -v

# Test specific graph tools
python -m pytest tests/test_graph_backup_unit.py::TestBackupGraphToDir -v
python -m pytest tests/test_handlers_unit.py::TestGraphManagementHandlers -v
```

### Complete Test Suite

```powershell
# Run all tests with coverage reporting
python -m pytest tests/ --cov=mcp_arangodb_async --cov-report=html --cov-report=term -v

# Run tests with specific markers
python -m pytest tests/ -m "not slow" -v  # Skip slow tests
python -m pytest tests/ -m "integration" -v  # Only integration tests
```

### Test Coverage Reporting

```powershell
# Generate detailed coverage report
python -m pytest tests/ --cov=mcp_arangodb_async --cov-report=html
# Open htmlcov/index.html in browser for detailed coverage analysis

# Terminal coverage summary
python -m pytest tests/ --cov=mcp_arangodb_async --cov-report=term-missing
```

### Debugging Test Failures

#### Common Issues and Solutions

1. **Database Connection Failures**
```powershell
# Verify ArangoDB is running and healthy
docker compose ps arangodb
python -m mcp_arangodb_async --health
```

2. **Import Errors**
```powershell
# Ensure package is properly installed
python -m pip install -e .
```

3. **Test Environment Issues**
```powershell
# Run tests with verbose logging
LOG_LEVEL=DEBUG python -m pytest tests/test_mcp_integration.py -v -s
```

4. **Specific Test Debugging**
```powershell
# Run single test with maximum verbosity
python -m pytest tests/test_graph_integration.py::TestGraphManagementIntegration::test_backup_graph_tool_success -vvv -s
```

### Test Performance Benchmarks

```powershell
# Run performance tests with timing
python -m pytest tests/ --durations=10 -v

# Profile test execution
python -m pytest tests/ --profile --profile-svg
```

### Interpreting Test Results

**Success Indicators:**
- All tests pass (green dots/checkmarks)
- Coverage >90% for new components
- No import or dependency errors
- Integration tests connect to database successfully

**Failure Investigation:**
- Check test output for specific assertion failures
- Verify database connectivity for integration tests
- Ensure all dependencies are installed
- Check for environment variable configuration issues

---

## Not Implemented (by Design)

- **Database creation/deletion** — Requires elevated privileges; handled by ops/IaC or setup scripts
- **Listing all databases** — Admin-only operation that can disclose tenant information
- **Direct file system access** — Security boundary maintained through controlled backup operations
- **User management operations** — Administrative functions outside application scope

These design choices reduce misuse potential, respect least privilege principles, and keep the server focused on application-level graph and data operations.

---

## Troubleshooting (PowerShell)

Common issues and their solutions during setup and operation.

### Environment Configuration Issues

**Wrong env vars or old values in session**

Symptoms: `python -m mcp_arangodb --health` shows db/user as `mcp_test`/`mcp_user` or unexpected values.

Fix:
```powershell
# Clear stale values to prefer .env
Remove-Item Env:ARANGO_URL,Env:ARANGO_DB,Env:ARANGO_USERNAME,Env:ARANGO_PASSWORD -ErrorAction SilentlyContinue
Remove-Item Env:ARANGO_USER,Env:ARANGO_PASS -ErrorAction SilentlyContinue
# Re-run from repo root so python-dotenv finds .env
python -m mcp_arangodb_async --health
```

### Authentication Issues

**HTTP 401 Unauthorized**

Symptom: `{"ok": false, "error": "[HTTP 401] not authorized"}`

Cause: App user/database not created or wrong password.

Fix:
```powershell
pwsh -File .\scripts\setup-arango.ps1
# If ARANGO_ROOT_PASSWORD differs from default 'changeme':
# pwsh -File .\scripts\setup-arango.ps1 -RootPassword "your_root_pw"
```

### Container Health Issues

**Container unhealthy (healthcheck fails)**

Symptom: `docker inspect ... Health.Log` shows connection failures.

Fix: Ensure your `docker-compose.yml` uses the correct healthcheck. Recreate container:
```powershell
docker compose down
docker compose up -d arangodb
docker compose ps arangodb
```

### MCP Client Issues

**MCP stdio client shows "Database unavailable"**

Causes and fixes:
- **Server started before DB ready**: Re-run; lazy connect attempts connection on first tool call
- **Environment not reaching child process**: Ensure `.env` exists at repo root
- **Verbose debugging**:
```powershell
$env:LOG_LEVEL="DEBUG"
python -m mcp_arangodb_async.entry
```

### Manual Verification

```powershell
# HTTP ping
curl http://localhost:8529/_api/version

# Test as app user
docker compose exec arangodb arangosh --server.username mcp_arangodb_user --server.password mcp_arangodb_password --server.database mcp_arangodb_test --javascript.execute-string "require('@arangodb').db._collections().map(c=>c.name())"

# Test graph tools
python .\scripts\mcp_stdio_client.py --demo --collection users
```

---

## Appendix A: License Notes (ArangoDB)

- **This repository**: Apache License 2.0
- **Development/Testing**: Primarily against ArangoDB 3.11
- **ArangoDB 3.12+ Licensing Changes**:
  - **Source code**: Business Source License 1.1 (BUSL-1.1)
  - **Community binaries**: ArangoDB Community License with usage limits
  - **Documentation**: https://docs.arangodb.com/3.12/release-notes/version-3.12/incompatible-changes-in-3-12/
  - **Community License**: https://arangodb.com/community-license/

**Important**: This repository does not grant rights to ArangoDB binaries. You must comply with ArangoDB's license for your deployment version.

---

## Appendix B: Python File Index

### Core Package Files
- **mcp_arangodb_async/__init__.py** — Package exports for public API (Config, helpers)
- **mcp_arangodb_async/__main__.py** — CLI entrypoint for quick checks; run via `python -m mcp_arangodb_async`
- **mcp_arangodb_async/config.py** — Configuration loader/validator (env + optional .env via python-dotenv)
- **mcp_arangodb_async/db.py** — DB client and database acquisition, health checks, connection helpers
- **mcp_arangodb_async/entry.py** — MCP stdio server bootstrap: lifecycle, tool registration, routing
- **mcp_arangodb_async/tools.py** — Centralized tool-name constants used across the server
- **mcp_arangodb_async/types.py** — TypedDicts/aliases maintained for typing and compatibility

### Data Operations
- **mcp_arangodb_async/handlers.py** — Tool implementations (CRUD, indexes, graphs, validation, queries)
- **mcp_arangodb_async/models.py** — Pydantic models for tool inputs and JSON Schemas
- **mcp_arangodb_async/backup.py** — Backup utilities (validate output dir; export collections to JSON)

### Graph Management
- **mcp_arangodb_async/graph_backup.py** — Advanced graph backup/restore utilities with integrity validation
- **mcp_arangodb_async/content_converter.py** — Flexible content conversion system for multiple output formats

### Utility Scripts
- **scripts/inspector.py** — Lightweight script for inspecting/diagnosing MCP I/O or environments
- **scripts/mcp_stdio_client.py** — Simple MCP stdio client for manual testing and demos
- **scripts/setup-arango.ps1** — PowerShell script for ArangoDB initialization

### Test Suite
#### Core Tests
- **tests/test_config_unit.py** — Configuration loading and validation tests
- **tests/test_db_unit.py** — Database connection and client tests
- **tests/test_models_unit.py** — Pydantic model validation tests
- **tests/test_handlers_unit.py** — Handler function unit tests
- **tests/test_mcp_integration.py** — MCP protocol integration tests

#### Specialized Tests
- **tests/test_backup.py** — Backup functionality tests
- **tests/test_graph_unit.py** — Basic graph operations tests
- **tests/test_graph_mgmt_unit.py** — Graph management unit tests
- **tests/test_add_vertex_alias_unit.py** — Graph alias functionality tests
- **tests/test_schema_and_query_tools_unit.py** — Schema and query tool tests

#### **Graph Management Tests**
- **tests/test_graph_backup_unit.py** — Graph backup/restore utility tests
- **tests/test_graph_integration.py** — Graph management MCP integration tests
- **tests/test_content_converter.py** — Content conversion system tests



---

## References

- **Source code**: `mcp_arangodb_async/` (entry.py, handlers.py, tools.py, graph_backup.py, content_converter.py)
- **Setup script**: `scripts/setup-arango.ps1`
- **Docker Compose**: `docker-compose.yml`
- **Documentation**:
  - [MCP specification](https://modelcontextprotocol.io/)
  - [Python Arango driver](https://github.com/ArangoDB-Community/python-arango)
  - [ArangoDB v3.11 docs](https://docs.arangodb.com/3.11/)
  - [ArangoDB v3.11Graph documentation](https://docs.arangodb.com/3.11/graphs/)
- **Tools**:
  - [Windows PowerShell](https://learn.microsoft.com/powershell/)
  - [Docker Desktop](https://www.docker.com/products/docker-desktop/)

---

## Contributing

This project follows established patterns for consistency and maintainability:

1. **Code Style**: Follow existing patterns in handlers.py and models.py
2. **Testing**: Add comprehensive unit and integration tests for new features
3. **Documentation**: Update docstrings and README for new functionality
4. **Backward Compatibility**: Ensure no breaking changes to existing tools

### Development Workflow

```powershell
# Setup development environment
python -m pip install -r requirements-dev.txt

# Run tests before committing
python -m pytest tests/ --cov=mcp_arangodb

# Check code quality
python -m flake8 mcp_arangodb/
python -m mypy mcp_arangodb/
```

---

*Enhanced ArangoDB MCP Server - Empowering AI assistants with advanced graph database capabilities*
