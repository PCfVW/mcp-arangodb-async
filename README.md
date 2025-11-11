# ArangoDB MCP Server for Python

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://github.com/PCfVW/mcp-arango-async/blob/master/LICENSE)
[![MCP](https://img.shields.io/badge/Protocol-MCP-%23555555)](https://modelcontextprotocol.io/)
[![PyPI](https://img.shields.io/pypi/v/mcp-arangodb-async)](https://pypi.org/project/mcp-arangodb-async/)

A production-ready Model Context Protocol (MCP) server exposing advanced ArangoDB operations to AI assistants like Claude Desktop and Augment Code. Features async-first Python architecture, comprehensive graph management, flexible content conversion (JSON, Markdown, YAML, Table), backup/restore functionality, and analytics capabilities.

---

## Quick Links

📚 **Documentation:** [https://github.com/PCfVW/mcp-arango-async/tree/master/docs](https://github.com/PCfVW/mcp-arango-async/tree/master/docs)

🚀 **Quick Start:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/quickstart-stdio.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/quickstart-stdio.md)

🔧 **Installation:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/installation.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/installation.md)

📖 **Tools Reference:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/tools-reference.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/tools-reference.md)

🎯 **MCP Design Patterns:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/mcp-design-patterns.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/mcp-design-patterns.md)

📝 **Changelog:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/changelog.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/changelog.md)

🐛 **Issues:** [https://github.com/PCfVW/mcp-arango-async/issues](https://github.com/PCfVW/mcp-arango-async/issues)

---

## Features

✅ **43 MCP Tools** - Complete ArangoDB operations (queries, collections, indexes, graphs)
✅ **MCP Design Patterns** - Progressive discovery, context switching, tool unloading (98.7% token savings)
✅ **Graph Management** - Create, traverse, backup/restore named graphs
✅ **Content Conversion** - JSON, Markdown, YAML, and Table formats
✅ **Backup/Restore** - Collection and graph-level backup with validation
✅ **Analytics** - Query profiling, explain plans, graph statistics
✅ **Dual Transport** - stdio (desktop clients) and HTTP (web/containerized)
✅ **Docker Support** - Run in Docker for isolation and reproducibility
✅ **Production-Ready** - Retry logic, graceful degradation, comprehensive error handling
✅ **Type-Safe** - Pydantic validation for all tool arguments

---

## Architecture

```
┌────────────────────┐      ┌─────────────────────┐       ┌──────────────────┐
│   MCP Client       │      │  ArangoDB MCP       │       │   ArangoDB       │
│ (Claude, Augment)  │─────▶│  Server (Python)    │─────▶│  (Docker)        │
│                    │      │  • 43 Tools         │       │  • Multi-Model   │
│                    │      │  • Graph Mgmt       │       │  • Graph Engine  │
│                    │      │  • MCP Patterns     │       │  • AQL Engine    │
└────────────────────┘      └─────────────────────┘       └──────────────────┘
```

---

## Installation

### Prerequisites

- **Python 3.11+**
- **Docker Desktop** (for ArangoDB)

### Quick Install

```bash
# Install from PyPI
pip install mcp-arangodb-async

# Start ArangoDB
docker run -d \
  --name arangodb \
  -p 8529:8529 \
  -e ARANGO_ROOT_PASSWORD=changeme \
  arangodb:3.11

# Verify installation
python -m mcp_arangodb_async --health
```

**Expected output:**
```json
{"status": "healthy", "database_connected": true, "database_info": {"version": "3.11.x", "name": "mcp_arangodb_test"}}
```

📖 **Detailed installation guide:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/installation.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/installation.md)

---

## Quick Start

### stdio Transport (Desktop Clients)

**1. Configure Claude Desktop**

Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/.config/Claude/claude_desktop_config.json` (macOS/Linux):

```json
{
  "mcpServers": {
    "arangodb": {
      "command": "python",
      "args": ["-m", "mcp_arangodb_async", "server"],
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

**2. Restart Claude Desktop**

**3. Test the connection:**

Ask Claude: *"List all collections in the ArangoDB database"*

📖 **Full stdio quickstart:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/quickstart-stdio.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/quickstart-stdio.md)

---

### Docker Container (Alternative)

**1. Build the Docker image:**

```bash
docker build -t mcp-arangodb-async:latest .
```

**2. Configure Claude Desktop:**

Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/.config/Claude/claude_desktop_config.json` (macOS/Linux):

```json
{
  "mcpServers": {
    "arangodb": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp-arangodb-async:latest"],
      "env": {
        "ARANGO_URL": "http://host.docker.internal:8529",
        "ARANGO_DB": "mcp_arangodb_test",
        "ARANGO_USERNAME": "mcp_arangodb_user",
        "ARANGO_PASSWORD": "mcp_arangodb_password"
      }
    }
  }
}
```

**3. Restart Claude Desktop**

📖 **Transport configuration guide:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/configuration/transport-configuration.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/configuration/transport-configuration.md)

---

### HTTP Transport (Web/Containerized)

**1. Start HTTP server:**

```bash
python -m mcp_arangodb_async --transport http --host 0.0.0.0 --port 8000
```

**2. Test health endpoint:**

```bash
curl http://localhost:8000/health
```

**3. Connect from web client:**

```javascript
import { MCPClient } from '@modelcontextprotocol/sdk';

const client = new MCPClient({
  transport: 'http',
  url: 'http://localhost:8000/mcp'
});

await client.connect();
const tools = await client.listTools();
```

📖 **HTTP transport guide:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/http-transport.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/http-transport.md)

---

## Configuration

### Environment Variables

**Required:**
```bash
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=root
ARANGO_PASSWORD=changeme
```

**Optional:**
```bash
# Transport configuration
MCP_TRANSPORT=stdio                    # stdio or http
MCP_HTTP_HOST=0.0.0.0                  # HTTP bind address
MCP_HTTP_PORT=8000                     # HTTP port
MCP_HTTP_STATELESS=false               # Stateless mode

# Connection tuning
ARANGO_TIMEOUT_SEC=30.0                # Request timeout
ARANGO_CONNECT_RETRIES=3               # Connection retries
ARANGO_CONNECT_DELAY_SEC=1.0           # Retry delay

# Logging
LOG_LEVEL=INFO                         # DEBUG, INFO, WARNING, ERROR
```

📖 **Complete configuration reference:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/configuration/environment-variables.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/configuration/environment-variables.md)

---

## Available Tools

The server exposes **43 MCP tools** organized into 10 categories:

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

### Graph Backup/Restore (4 tools)
- `arango_backup_graph` - Backup single graph
- `arango_restore_graph` - Restore single graph
- `arango_backup_named_graphs` - Backup all named graphs
- `arango_validate_graph_integrity` - Validate graph integrity

### Analytics (2 tools)
- `arango_graph_statistics` - Graph statistics
- `arango_database_status` - Database status

### MCP Design Pattern Tools (9 tools)
- `arango_search_tools` - Search for tools by keywords
- `arango_list_tools_by_category` - List tools by category
- `arango_switch_context` - Switch workflow context
- `arango_get_active_context` - Get active context
- `arango_list_contexts` - List all contexts
- `arango_advance_workflow_stage` - Advance workflow stage
- `arango_get_tool_usage_stats` - Get tool usage statistics
- `arango_unload_tools` - Unload specific tools
- `arango_graph_traversal` - Alias for arango_traverse

📖 **Complete tools reference:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/tools-reference.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/tools-reference.md)

📖 **MCP Design Patterns Guide:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/mcp-design-patterns.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/mcp-design-patterns.md)

---

## Use Case Example: Codebase Graph Analysis

Model your codebase as a graph to analyze dependencies, find circular references, and understand architecture:

```python
# 1. Create graph structure
Ask Claude: "Create a graph called 'codebase' with vertex collections 'modules' and 'functions', 
and edge collection 'calls' connecting functions"

# 2. Import codebase data
Ask Claude: "Insert these modules into the 'modules' collection: [...]"

# 3. Analyze dependencies
Ask Claude: "Find all functions that depend on the 'auth' module using graph traversal"

# 4. Detect circular dependencies
Ask Claude: "Check for circular dependencies in the codebase graph"

# 5. Generate architecture diagram
Ask Claude: "Export the codebase graph structure as Markdown for visualization"
```

📖 **More examples:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/examples/codebase-analysis.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/examples/codebase-analysis.md)

---

## Documentation

### Getting Started
- [Installation Guide](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/installation.md)
- [Quick Start (stdio)](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/quickstart-stdio.md)
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
python -m mcp_arangodb_async --health
```

**Server won't start in Claude Desktop:**
```bash
# Verify Python installation
python --version  # Must be 3.11+

# Test module directly
python -m mcp_arangodb_async --health

# Check Claude Desktop logs
# Windows: %APPDATA%\Claude\logs\
# macOS: ~/Library/Logs/Claude/
```

**Tool execution errors:**
- Verify ArangoDB is healthy: `docker compose ps`
- Check environment variables are set correctly
- Review server logs for detailed error messages

📖 **Complete troubleshooting guide:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/troubleshooting.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/user-guide/troubleshooting.md)

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

📖 **License details:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/installation.md#arangodb-licensing](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/getting-started/installation.md#arangodb-licensing)

---

## Contributing

Contributions are welcome! Please see our documentation for guidelines.

📖 **Architecture decisions:** [https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/low-level-mcp-rationale.md](https://github.com/PCfVW/mcp-arango-async/blob/master/docs/developer-guide/low-level-mcp-rationale.md)

---

## Support

- **Issues:** [https://github.com/PCfVW/mcp-arango-async/issues](https://github.com/PCfVW/mcp-arango-async/issues)
- **Discussions:** [https://github.com/PCfVW/mcp-arango-async/discussions](https://github.com/PCfVW/mcp-arango-async/discussions)
- **Documentation:** [https://github.com/PCfVW/mcp-arango-async/tree/master/docs](https://github.com/PCfVW/mcp-arango-async/tree/master/docs)

---

## Acknowledgments

Built with:
- [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic
- [python-arango](https://github.com/ArangoDB-Community/python-arango) - Official ArangoDB Python driver
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Starlette](https://www.starlette.io/) - HTTP transport
- [ArangoDB](https://www.arangodb.com/) - Multi-model database

