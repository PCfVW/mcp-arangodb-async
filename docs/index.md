# Documentation Hub

Complete documentation for mcp-arangodb-async - A Model Context Protocol server for ArangoDB.

---

## Quick Navigation

| I want to... | Start here |
|--------------|------------|
| **Get started quickly** | [Quickstart Guide](getting-started/quickstart.md) |
| **Install ArangoDB** | [ArangoDB Installation](getting-started/install-arangodb.md) |
| **See all available tools** | [Tools Reference](user-guide/tools-reference.md) |
| **Configure HTTP transport** | [Transport Configuration](configuration/transport-configuration.md) |
| **Troubleshoot issues** | [Troubleshooting Guide](user-guide/troubleshooting.md) |
| **Understand the architecture** | [Architecture Overview](developer-guide/architecture.md) |
| **Contribute to the project** | [Contributing Guide](../CONTRIBUTING.md) |

---

## Documentation Structure

### 📚 Getting Started (New Users)

Start here if you're new to mcp-arangodb-async.

1. **[ArangoDB Installation](getting-started/install-arangodb.md)** (10 min)
   - Docker installation
   - Database and user setup

2. **[Quickstart Guide](getting-started/quickstart.md)** (10 min)
   - Install from PyPI
   - Configure MCP clients (stdio and HTTP)
   - Health check verification

3. **[First Interaction](getting-started/first-interaction.md)** (15 min)
   - Test prompts for verification
   - AI-coding use case examples
   - Troubleshooting test failures

---

### 📖 User Guide (End Users)

Complete reference for using the server.

1. **[Tools Reference](user-guide/tools-reference.md)** (30 min)
   - All 46 MCP tools documented
   - 10 categories: CRUD, Queries, Collections, Indexes, Graphs, Analytics, Backup, Content, Database, MCP Patterns
   - Arguments, return values, examples

2. **[MCP Design Patterns Guide](user-guide/mcp-design-patterns.md)** (45-60 min)
   - Progressive Tool Discovery - Load tools on-demand (98.7% token savings)
   - Context Switching - Switch between workflow-specific tool sets
   - Tool Unloading - Remove tools as workflows progress
   - Combining patterns for complex workflows
   - Toolset configuration (baseline vs full)

3. **[Troubleshooting Guide](user-guide/troubleshooting.md)** (20 min)
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
   - Centralized routing for 46+ tools
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

### Path 1: End User

**Goal:** Use mcp-arangodb-async with MCP Hosts (Claude Desktop, Augment Code, etc.)

**Time:** 30-40 minutes

1. [ArangoDB Installation](getting-started/install-arangodb.md) → Set up ArangoDB
2. [Quickstart Guide](getting-started/quickstart.md) → Install and configure MCP client
3. [First Interaction](getting-started/first-interaction.md) → Test with prompts
4. [Tools Reference](user-guide/tools-reference.md) → Learn available tools
5. [Codebase Analysis Example](examples/codebase-analysis.md) → Advanced graph usage
6. [Troubleshooting Guide](user-guide/troubleshooting.md) → Fix issues

---

### Path 2: Developer

**Goal:** Integrate mcp-arangodb-async into a web application

**Time:** 60-90 minutes

1. [Install from Source](getting-started/install-from-source.md) → Set up development environment
2. [Architecture Overview](developer-guide/architecture.md) → Understand system design
3. [HTTP Transport Implementation](developer-guide/http-transport.md) → Learn HTTP transport
4. [Transport Configuration](configuration/transport-configuration.md) → Configure HTTP transport
5. [Environment Variables](configuration/environment-variables.md) → Configure for production
6. [Troubleshooting Guide](user-guide/troubleshooting.md) → Debug issues

---

### Path 3: DevOps Engineer

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

1. [Install from Source](getting-started/install-from-source.md) → Set up development environment
2. [Architecture Overview](developer-guide/architecture.md) → Understand codebase structure
3. [Low-Level MCP Rationale](developer-guide/low-level-mcp-rationale.md) → Understand design decisions
4. [HTTP Transport Implementation](developer-guide/http-transport.md) → Learn transport layer
5. [Changelog](developer-guide/changelog.md) → Review version history
6. [Contributing Guide](../CONTRIBUTING.md) → Follow contribution workflow

---

## Support

### Getting Help

- **Documentation:** You're reading it! 📖
- **GitHub Issues:** [Report bugs or request features](https://github.com/PCfVW/mcp-arango-async/issues)
- **GitHub Discussions:** [Ask questions or share ideas](https://github.com/PCfVW/mcp-arango-async/discussions)

### Before Asking for Help

1. Check [Troubleshooting Guide](user-guide/troubleshooting.md)
2. Search [existing issues](https://github.com/PCfVW/mcp-arango-async/issues)
3. Test with health check: `maa health`
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

**Last Updated:** 2025-12-13
