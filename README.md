<!-- mcp-name: io.github.PCfVW/mcp-arangodb-async -->

# ArangoDB MCP Server for Python

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://github.com/PCfVW/mcp-arango-async/blob/master/LICENSE)
[![MCP](https://img.shields.io/badge/Protocol-MCP-%23555555)](https://modelcontextprotocol.io/)
[![PyPI](https://img.shields.io/pypi/v/mcp-arangodb-async)](https://pypi.org/project/mcp-arangodb-async/)

A production-ready Model Context Protocol (MCP) server exposing advanced ArangoDB operations to AI assistants like Claude Desktop and Augment Code. Features async-first Python architecture, comprehensive graph management, flexible content conversion (JSON, Markdown, YAML, Table), backup/restore functionality, and analytics capabilities.

---

## Quick Links

📚 **Documentation:** [https://github.com/PCfVW/mcp-arango-async/tree/master/docs](https://github.com/PCfVW/mcp-arango-async/tree/master/docs)

🚀 **Quick Start:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/quickstart.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/quickstart.md)

🔧 **ArangoDB Setup:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/install-arangodb.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/install-arangodb.md)

🗄️ **Multi-Tenancy Guide:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/multi-tenancy-guide.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/multi-tenancy-guide.md)

⚙️ **CLI Reference:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/cli-reference.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/cli-reference.md)

📖 **Tools Reference:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/tools-reference.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/tools-reference.md)

🎯 **MCP Design Patterns:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/mcp-design-patterns.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/mcp-design-patterns.md)

📝 **Changelog:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/changelog.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/changelog.md)

🐛 **Issues:** [https://github.com/PCfVW/mcp-arango-async/issues](https://github.com/PCfVW/mcp-arango-async/issues)

---

## Features

- ✅ **46 MCP Tools** - Complete ArangoDB operations (queries, collections, indexes, graphs)
- ✅ **Multi-Tenancy** - Work with multiple databases, environment switching, cross-database operations
- ✅ **MCP Design Patterns** - Progressive discovery, context switching, tool unloading (98.7% token savings)
- ✅ **Graph Management** - Create, traverse, backup/restore named graphs
- ✅ **Content Conversion** - JSON, Markdown, YAML, and Table formats
- ✅ **Backup/Restore** - Collection and graph-level backup with validation
- ✅ **Analytics** - Query profiling, explain plans, graph statistics
- ✅ **Dual Transport** - stdio (desktop clients) and HTTP (web/containerized)
- ✅ **Docker Support** - Run in Docker for isolation and reproducibility
- ✅ **Production-Ready** - Retry logic, graceful degradation, comprehensive error handling
- ✅ **Type-Safe** - Pydantic validation for all tool arguments

---

## Architecture

```
┌────────────────────┐      ┌─────────────────────┐       ┌──────────────────┐
│   MCP Client       │      │  ArangoDB MCP       │       │   ArangoDB       │
│ (Claude, Augment)  │─────▶│  Server (Python)    │─────▶│  (Docker)        │
│                    │      │  • 46 Tools         │       │  • Multi-Model   │
│                    │      │  • Multi-Tenancy    │       │  • Graph Engine  │
│                    │      │  • Graph Mgmt       │       │  • AQL Engine    │
│                    │      │  • MCP Patterns     │       │                  │
└────────────────────┘      └─────────────────────┘       └──────────────────┘
```

---

## Getting Started with ArangoDB

### Prerequisites

- **Docker and Docker Compose** installed
- **Python 3.11+** (for mcp-arangodb-async)

### Step 1: Install ArangoDB

Create a `docker-compose.yml` file:

```yaml
services:
  arangodb:
    image: arangodb:3.11
    environment:
      ARANGO_ROOT_PASSWORD: ${ARANGO_ROOT_PASSWORD:-changeme}
    ports:
      - "8529:8529"
    volumes:
      - arangodb_data:/var/lib/arangodb3
      - arangodb_apps:/var/lib/arangodb3-apps
    healthcheck:
      test: arangosh --server.username root --server.password "$ARANGO_ROOT_PASSWORD" --javascript.execute-string "require('@arangodb').db._version()" > /dev/null 2>&1 || exit 1
      interval: 5s
      timeout: 2s
      retries: 30
    restart: unless-stopped

volumes:
  arangodb_data:
    driver: local
  arangodb_apps:
    driver: local
```

Create a `.env` file:

```bash
# ArangoDB root password
ARANGO_ROOT_PASSWORD=changeme

# MCP Server connection settings
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
```

Start ArangoDB:

```bash
docker compose --env-file .env up -d
```

### Step 2: Install mcp-arangodb-async

Install the MCP server package:

```bash
pip install mcp-arangodb-async
```

<details>
<summary><b>Alternative: Install with Conda/Mamba/Micromamba</b></summary>

```bash
# Create environment and install
conda create -n mcp-arango python=3.11
conda activate mcp-arango
pip install mcp-arangodb-async

# Or with mamba/micromamba:
# mamba create -n mcp-arango python=3.11
# mamba activate mcp-arango
# pip install mcp-arangodb-async
```

</details>

<details>
<summary><b>Alternative: Install with uv</b></summary>

```bash
# Create environment and install
uv venv .venv --python 3.11
uv pip install mcp-arangodb-async
```

</details>

### Step 3: Create Database and User

Create the database and user for the MCP server:

```bash
maa db add mcp_arangodb_test \
  --url http://localhost:8529 \
  --with-user mcp_arangodb_user \
  --env-file .env
```

**Expected output:**
```
The following actions will be performed:
  [ADD] Database 'mcp_arangodb_test'
  [ADD] User 'mcp_arangodb_user' (active: true)
  [GRANT] Permission rw: mcp_arangodb_user → mcp_arangodb_test

Are you sure you want to proceed? [y/N]: y
db add:
[ADDED] Database 'mcp_arangodb_test'
[ADDED] User 'mcp_arangodb_user' (active: true)
[GRANTED] Permission rw: mcp_arangodb_user → mcp_arangodb_test
```

Verify the database connection:

```bash
# Set environment variables
export ARANGO_URL=http://localhost:8529
export ARANGO_DB=mcp_arangodb_test
export ARANGO_USERNAME=mcp_arangodb_user
export ARANGO_PASSWORD=mcp_arangodb_password

# Run health check
maa health
```

**Expected output:**
```json
{"status": "healthy", "database_connected": true, "database_info": {"version": "3.11.x", "name": "mcp_arangodb_test"}}
```

### Step 4: Configure MCP Host

Configure your MCP host to use the server. The configuration includes environment variables for database connection. The location of the configuration file depends on your MCP host. For Claude Desktop, the file is located at:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Configuration:**

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

<details>
<summary><b>Alternative: Configuration for Conda/Mamba/Micromamba</b></summary>

If you installed with conda/mamba/micromamba, use the `run` command:

```json
{
  "mcpServers": {
    "arangodb": {
      "command": "conda",
      "args": ["run", "-n", "mcp-arango", "maa", "server"],
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

Replace `"conda"` with `"mamba"` or `"micromamba"` if using those tools.

</details>

<details>
<summary><b>Alternative: Configuration for uv</b></summary>

If you installed with uv, use `uv run`:

```json
{
  "mcpServers": {
    "arangodb": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/project", "maa", "server"],
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

Replace `/path/to/project` with the directory containing your `.venv` folder.

</details>

**Restart your MCP client** after updating the configuration.

**Test the connection:**

Ask your MCP client: *"List all collections in the ArangoDB database"*

The assistant should successfully connect and list your collections.

## Available Tools

The server exposes **46 MCP tools** organized into 11 categories:

### Multi-Tenancy Tools (4 tools)
- `arango_set_focused_database` - Set focused database for session
- `arango_get_focused_database` - Get currently focused database
- `arango_list_available_databases` - List all configured databases
- `arango_get_database_resolution` - Show database resolution algorithm

### Core Data Operations (7 tools)
- `arango_query` - Execute AQL queries
- `arango_list_collections` - List all collections
- `arango_insert` - Insert documents
- `arango_update` - Update documents
- `arango_remove` - Remove documents
- `arango_create_collection` - Create collections
- `arango_backup` - Backup collections

### Index Management (3 tools)
- `arango_list_indexes` - List indexes
- `arango_create_index` - Create indexes
- `arango_delete_index` - Delete indexes

### Query Analysis (3 tools)
- `arango_explain_query` - Explain query execution plan
- `arango_query_builder` - Build AQL queries
- `arango_query_profile` - Profile query performance

### Data Validation (4 tools)
- `arango_validate_references` - Validate document references
- `arango_insert_with_validation` - Insert with validation
- `arango_create_schema` - Create JSON schemas
- `arango_validate_document` - Validate against schema

### Bulk Operations (2 tools)
- `arango_bulk_insert` - Bulk insert documents
- `arango_bulk_update` - Bulk update documents

### Graph Management (7 tools)
- `arango_create_graph` - Create named graphs
- `arango_list_graphs` - List all graphs
- `arango_add_vertex_collection` - Add vertex collections
- `arango_add_edge_definition` - Add edge definitions
- `arango_add_vertex` - Add vertices
- `arango_add_edge` - Add edges
- `arango_graph_traversal` - Traverse graphs

### Graph Traversal (2 tools)
- `arango_traverse` - Graph traversal
- `arango_shortest_path` - Find shortest paths

### Graph Backup/Restore (5 tools)
- `arango_backup_graph` - Backup single graph
- `arango_restore_graph` - Restore single graph
- `arango_backup_named_graphs` - Backup all named graphs
- `arango_validate_graph_integrity` - Validate graph integrity
- `arango_graph_statistics` - Graph statistics

### Health & Status (1 tool)
- `arango_database_status` - Get comprehensive status of all databases

### Tool Aliases (2 tools)
- `arango_graph_traversal` - Alias for arango_traverse
- `arango_add_vertex` - Alias for arango_insert

### MCP Design Pattern Tools (8 tools)
- `arango_search_tools` - Search for tools by keywords
- `arango_list_tools_by_category` - List tools by category
- `arango_switch_workflow` - Switch workflow context
- `arango_get_active_workflow` - Get active workflow
- `arango_list_workflows` - List all workflows
- `arango_advance_workflow_stage` - Advance workflow stage
- `arango_get_tool_usage_stats` - Get tool usage statistics
- `arango_unload_tools` - Unload specific tools

📖 **Complete tools reference:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/tools-reference.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/tools-reference.md)

📖 **MCP Design Patterns Guide:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/mcp-design-patterns.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/mcp-design-patterns.md)

---

## Use Case Example: Codebase Graph Analysis

Model your codebase as a graph to analyze dependencies, find circular references, and understand architecture. Here is an excerpt from the longer [codebase analysis example](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/examples/codebase-analysis.md):

```python
# 1. Create graph structure
Ask Claude: "Create a graph called 'codebase' with vertex collections 'modules' and 'functions', and edge collection 'calls' connecting functions"

# 2. Import codebase data
Ask Claude: "Insert these modules into the 'modules' collection: [...]"

# 3. Analyze dependencies
Ask Claude: "Find all functions that depend on the 'auth' module using graph traversal"

# 4. Detect circular dependencies
Ask Claude: "Check for circular dependencies in the codebase graph"

# 5. Generate architecture diagram
Ask Claude: "Export the codebase graph structure as Markdown for visualization"
```

📖 [More examples](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/examples/codebase-analysis.md)

---

## Documentation

### Getting Started
- [ArangoDB Installation](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/install-arangodb.md)
- [Quickstart Guide](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/quickstart.md)
- [Install from Source](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/install-from-source.md)
- [First Interaction](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/first-interaction.md)

### Configuration
- [Transport Configuration](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/configuration/transport-configuration.md)
- [Environment Variables](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/configuration/environment-variables.md)

### User Guide
- [Tools Reference](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/tools-reference.md)
- [Troubleshooting](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/troubleshooting.md)

### Developer Guide
- [Architecture Overview](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/architecture.md)
- [Low-Level MCP Rationale](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/low-level-mcp-rationale.md)
- [HTTP Transport](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/http-transport.md)
- [Changelog](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/changelog.md)

### Examples
- [Codebase Dependency Analysis](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/examples/codebase-analysis.md)

📖 **Full documentation:** [https://github.com/PCfVW/mcp-arango-async/tree/master/docs](https://github.com/PCfVW/mcp-arango-async/tree/master/docs)

---

## Troubleshooting

### Common Issues

**Database connection fails:**
```bash
# Check ArangoDB is running
docker ps | grep arangodb

# Test connection
curl http://localhost:8529/_api/version

# Check credentials
maa health
```

**Server won't start in Claude Desktop:**
```bash
# Verify Python installation
python --version  # Must be 3.11+

# Test module directly
maa health

# Check Claude Desktop logs
# Windows: %APPDATA%\Claude\logs\
# macOS: ~/Library/Logs/Claude/
```

**Tool execution errors:**
- Verify ArangoDB is healthy: `docker compose ps`
- Check environment variables are set correctly
- Review server logs for detailed error messages

📖 [Complete troubleshooting guide](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/troubleshooting.md)

---

## Why Docker for ArangoDB?

✅ **Stability** - Isolated environment, no host conflicts  
✅ **Zero-install** - Start/stop with `docker compose`  
✅ **Reproducibility** - Same image across all environments  
✅ **Health checks** - Built-in readiness validation  
✅ **Fast reset** - Recreate clean instances easily  
✅ **Portability** - Consistent on Windows/macOS/Linux

---

## License

- **This project:** Apache License 2.0
- **ArangoDB 3.11:** Apache License 2.0
- **ArangoDB 3.12+:** Business Source License 1.1 (BUSL-1.1)

⚠️ **Important:** This repository does not grant rights to ArangoDB binaries. You must comply with ArangoDB's license for your deployment version.

📖 [License details](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/install-arangodb.md#licensing-considerations)

---

## Contributing

Contributions are welcome! Please see our documentation for guidelines.

📖 [Architecture decisions](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/low-level-mcp-rationale.md)

---

## Support

- [Issues](https://github.com/PCfVW/mcp-arango-async/issues)
- [Discussions](https://github.com/PCfVW/mcp-arango-async/discussions)
- [Documentation](https://github.com/PCfVW/mcp-arango-async/tree/master/docs)

---

## Acknowledgments

Built with:
- [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- [python-arango](https://github.com/ArangoDB-Community/python-arango) - Official ArangoDB Python driver
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Starlette](https://www.starlette.io/) - HTTP transport
- [ArangoDB](https://www.arangodb.com/) - Multi-model database

