# Documentation Hub

Complete documentation for mcp-arangodb-async - A Model Context Protocol server for ArangoDB.

---

## Quick Navigation

| I want to... | Start here |
|--------------|------------|
| **Get started quickly** | [Quick Start (stdio)](#quick-start) |
| **Install the server** | [Installation Guide](getting-started/installation.md) |
| **See all available tools** | [Tools Reference](user-guide/tools-reference.md) |
| **Configure HTTP transport** | [Transport Configuration](configuration/transport-configuration.md) |
| **Troubleshoot issues** | [Troubleshooting Guide](user-guide/troubleshooting.md) |
| **Understand the architecture** | [Architecture Overview](developer-guide/architecture.md) |
| **Contribute to the project** | [Contributing Guide](#contributing) |

---

## Documentation Structure

### 📚 Getting Started (New Users)

Start here if you're new to mcp-arangodb-async.

1. **[Installation Guide](getting-started/installation.md)** (15 min)
   - Prerequisites and system requirements
   - Python environment setup
   - ArangoDB Docker installation
   - Database initialization
   - Health check verification

2. **[Quick Start (stdio)](getting-started/quickstart-stdio.md)** (10 min)
   - Fastest path to first interaction
   - Claude Desktop configuration
   - Augment Code configuration
   - First tool execution

3. **[First Interaction](getting-started/first-interaction.md)** (15 min)
   - Test prompts for verification
   - AI-coding use case examples
   - Troubleshooting test failures

---

### 📖 User Guide (End Users)

Complete reference for using the server.

1. **[Tools Reference](user-guide/tools-reference.md)** (30 min)
   - All 43 MCP tools documented
   - 10 categories: CRUD, Queries, Collections, Indexes, Graphs, Analytics, Backup, Content, Database, MCP Patterns
   - Arguments, return values, examples

2. **[MCP Design Patterns Guide](user-guide/mcp-design-patterns.md)** (45-60 min)
   - Progressive Tool Discovery - Load tools on-demand (98.7% token savings)
   - Context Switching - Switch between workflow-specific tool sets
   - Tool Unloading - Remove tools as workflows progress
   - Combining patterns for complex workflows
   - Toolset configuration (baseline vs full)

2. **[Troubleshooting Guide](user-guide/troubleshooting.md)** (20 min)
   - ArangoDB connection issues
   - MCP client configuration errors
   - Transport issues (stdio and HTTP)
   - Tool execution errors
   - Performance issues
   - Docker issues

---

### ⚙️ Configuration (Setup & Deployment)

Configure the server for different environments.

1. **[Transport Configuration](configuration/transport-configuration.md)** (25 min)
   - stdio transport setup (Claude Desktop, Augment Code)
   - HTTP transport setup (Docker, Kubernetes)
   - Client integration guides (JavaScript, Python)
   - Troubleshooting transport issues

2. **[Environment Variables](configuration/environment-variables.md)** (15 min)
   - Complete reference for all variables
   - ArangoDB connection variables
   - MCP transport variables
   - Connection tuning variables
   - Configuration methods (.env, shell, Docker)

---

### 💡 Examples (Real-World Use Cases)

Sophisticated examples demonstrating advanced capabilities.

1. **[Codebase Dependency Analysis](examples/codebase-analysis.md)** (45-60 min)
   - Graph modeling for software architecture
   - Dependency analysis and circular detection
   - Impact analysis for refactoring
   - Function call chain analysis
   - Module complexity scoring

---

### 🏗️ Developer Guide (Contributors & Advanced Users)

Understand the internals and contribute to the project.

1. **[Architecture Overview](developer-guide/architecture.md)** (25 min)
   - High-level architecture diagram
   - Component architecture (Entry Point, Tool Registry, Handlers, Database)
   - Data flow (tool execution, startup, error handling)
   - Design patterns (Decorator, Registry, Singleton, Strategy, Context Manager)
   - Technology stack

2. **[Low-Level MCP Rationale](developer-guide/low-level-mcp-rationale.md)** (20 min)
   - Why low-level Server API instead of FastMCP
   - Complex startup logic with retry/reconnect
   - Runtime state modification
   - Centralized routing for 34+ tools
   - Test suite compatibility
   - When to use each approach

3. **[HTTP Transport Implementation](developer-guide/http-transport.md)** (30 min)
   - Starlette application architecture
   - StreamableHTTPSessionManager usage
   - Stateful vs stateless modes
   - CORS configuration
   - Deployment (Docker Compose, Kubernetes)
   - Security considerations
   - Migration from stdio

4. **[Changelog](developer-guide/changelog.md)** (15 min)
   - Version history (0.1.x to 0.2.7)
   - Breaking changes and new features
   - Migration guides for each version
   - Versioning policy

---

## Learning Paths

### Path 1: End User (Desktop AI Client)

**Goal:** Use mcp-arangodb-async with Claude Desktop or Augment Code

**Time:** 30-40 minutes

1. [Installation Guide](getting-started/installation.md) → Install Python, ArangoDB, and server
2. [Quick Start (stdio)](getting-started/quickstart-stdio.md) → Configure Claude Desktop
3. [First Interaction](getting-started/first-interaction.md) → Test with prompts
4. [Tools Reference](user-guide/tools-reference.md) → Learn available tools
5. [Codebase Analysis Example](examples/codebase-analysis.md) → Advanced graph usage
6. [Troubleshooting Guide](user-guide/troubleshooting.md) → Fix issues

---

### Path 2: Developer (Web Application)

**Goal:** Integrate mcp-arangodb-async into a web application

**Time:** 60-90 minutes

1. [Installation Guide](getting-started/installation.md) → Set up development environment
2. [Architecture Overview](developer-guide/architecture.md) → Understand system design
3. [HTTP Transport Implementation](developer-guide/http-transport.md) → Learn HTTP transport
4. [Transport Configuration](configuration/transport-configuration.md) → Configure HTTP transport
5. [Environment Variables](configuration/environment-variables.md) → Configure for production
6. [Troubleshooting Guide](user-guide/troubleshooting.md) → Debug issues

---

### Path 3: DevOps Engineer (Production Deployment)

**Goal:** Deploy mcp-arangodb-async to Kubernetes

**Time:** 45-60 minutes

1. [Architecture Overview](developer-guide/architecture.md) → Understand components
2. [HTTP Transport Implementation](developer-guide/http-transport.md) → Learn stateless mode
3. [Transport Configuration](configuration/transport-configuration.md) → Kubernetes deployment
4. [Environment Variables](configuration/environment-variables.md) → Production configuration
5. [Troubleshooting Guide](user-guide/troubleshooting.md) → Monitor and debug

---

### Path 4: Contributor (Open Source)

**Goal:** Contribute to mcp-arangodb-async

**Time:** 90-120 minutes

1. [Installation Guide](getting-started/installation.md) → Set up development environment
2. [Architecture Overview](developer-guide/architecture.md) → Understand codebase structure
3. [Low-Level MCP Rationale](developer-guide/low-level-mcp-rationale.md) → Understand design decisions
4. [HTTP Transport Implementation](developer-guide/http-transport.md) → Learn transport layer
5. [Changelog](developer-guide/changelog.md) → Review version history
6. [Contributing Guide](#contributing) → Follow contribution workflow

---

## Quick Start

### Prerequisites

- Python 3.11 or 3.12
- Docker Desktop (for ArangoDB)
- Claude Desktop or Augment Code (for stdio transport)

### Installation (5 minutes)

```bash
# 1. Install server
pip install mcp-arangodb-async

# 2. Start ArangoDB
docker compose up -d arangodb

# 3. Initialize database
pwsh -File scripts/setup-arango.ps1 -RootPassword "changeme"

# 4. Test health
python -m mcp_arangodb_async --health
```

### Configure Claude Desktop (2 minutes)

**Edit `claude_desktop_config.json`:**

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

**Restart Claude Desktop** and verify server appears in MCP servers list.

### First Interaction (1 minute)

**Prompt Claude:**
```
List all available ArangoDB tools
```

**Expected:** Claude lists 43 tools in 10 categories.

---

## Key Concepts

### MCP (Model Context Protocol)

Protocol for AI assistants to interact with external tools and services. mcp-arangodb-async implements an MCP server that exposes ArangoDB operations as tools.

**Learn more:** [MCP Specification](https://modelcontextprotocol.io/)

---

### Transport Types

**stdio (Standard Input/Output):**
- For desktop AI clients (Claude Desktop, Augment Code)
- Process-based communication
- Default transport

**HTTP (Hypertext Transfer Protocol):**
- For web applications and containerized deployments
- Network-based communication
- Supports horizontal scaling

**Learn more:** [Transport Configuration](configuration/transport-configuration.md)

---

### ArangoDB 3.11

Multi-model database supporting documents, graphs, and key-value data. Version 3.11 uses Apache License 2.0 (open source).

**Learn more:** [ArangoDB Documentation](https://docs.arangodb.com/3.11/)

---

### Tool Categories

1. **CRUD Operations** - Create, read, update, delete documents
2. **Query Operations** - Execute AQL queries with profiling
3. **Collection Management** - Create, list, delete collections
4. **Index Management** - Create, list, delete indexes
5. **Graph Operations** - Create, traverse, manage named graphs
6. **Analytics** - Query profiling, explain plans, statistics
7. **Backup & Restore** - Collection and graph-level backup
8. **Content Conversion** - JSON, Markdown, YAML, Table formats
9. **Database Operations** - List databases, collections, indexes

**Learn more:** [Tools Reference](user-guide/tools-reference.md)

---

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# 1. Clone repository
git clone https://github.com/PCfVW/mcp-arango-async.git
cd mcp-arango-async

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# 4. Start ArangoDB
docker compose up -d arangodb

# 5. Run tests
pytest tests/
```

### Contribution Workflow

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/my-feature`
3. **Make** your changes
4. **Test** your changes: `pytest tests/`
5. **Format** code: `black .` and `ruff check .`
6. **Commit** with clear message: `git commit -m "feat: add new feature"`
7. **Push** to your fork: `git push origin feature/my-feature`
8. **Create** a Pull Request

### Code Style

- **Formatter:** black (line length: 88)
- **Linter:** ruff
- **Type hints:** Required for public APIs
- **Docstrings:** Required for public functions/classes

### Testing

- **Framework:** pytest
- **Coverage:** Aim for >80%
- **Test types:** Unit tests, integration tests
- **Run tests:** `pytest tests/`

---

## Support

### Getting Help

- **Documentation:** You're reading it! 📖
- **GitHub Issues:** [Report bugs or request features](https://github.com/PCfVW/mcp-arango-async/issues)
- **GitHub Discussions:** [Ask questions or share ideas](https://github.com/PCfVW/mcp-arango-async/discussions)

### Before Asking for Help

1. Check [Troubleshooting Guide](user-guide/troubleshooting.md)
2. Search [existing issues](https://github.com/PCfVW/mcp-arango-async/issues)
3. Test with `--health` flag: `python -m mcp_arangodb_async --health`
4. Review logs (set `LOG_LEVEL=DEBUG`)

---

## License

Apache License 2.0 - See [LICENSE](../LICENSE) file for details.

---

## Acknowledgments

- **MCP SDK:** [Anthropic's Model Context Protocol](https://modelcontextprotocol.io/)
- **ArangoDB:** [Multi-model database](https://www.arangodb.com/)
- **python-arango:** [Python driver for ArangoDB](https://github.com/ArangoDB-Community/python-arango)

---

**Last Updated:** 2025-10-20  
**Documentation Version:** 1.0  
**Project Version:** 0.2.7

