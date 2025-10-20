# Changelog

All notable changes to the mcp-arangodb-async project.

**Audience:** End Users and Developers  
**Prerequisites:** None  
**Estimated Time:** 10-15 minutes

---

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## Table of Contents

1. [Version 0.2.7 (Current)](#version-027---2025-10-19)
2. [Version 0.2.6](#version-026---2025-10-15)
3. [Version 0.2.5](#version-025---2025-10-10)
4. [Version 0.2.0-0.2.4](#version-020-024---2025-09-01-to-2025-10-01)
5. [Version 0.1.x](#version-01x---2025-08-01)
6. [Migration Guides](#migration-guides)

---

## [0.2.7] - 2025-10-19

**Current Release**

### Added

✅ **HTTP Transport Phase 2: CLI Arguments and Environment Variables**
- Command-line arguments for transport configuration:
  - `--transport` - Select stdio or HTTP transport
  - `--host` - HTTP bind address (default: 0.0.0.0)
  - `--port` - HTTP port number (default: 8000)
  - `--stateless` - Enable stateless mode for horizontal scaling
- Environment variables for HTTP transport:
  - `MCP_TRANSPORT` - Transport type (stdio or http)
  - `MCP_HTTP_HOST` - HTTP bind address
  - `MCP_HTTP_PORT` - HTTP port number
  - `MCP_HTTP_STATELESS` - Stateless mode flag
  - `MCP_HTTP_CORS_ORIGINS` - CORS allowed origins

✅ **Version Bump Script**
- Automated version management: `scripts/bump_version.py`
- Updates both `pyproject.toml` and `entry.py` atomically
- Semantic versioning validation
- Dry-run mode for preview

✅ **Enhanced Testing**
- 37 new tests for transport configuration
- CLI argument parsing tests
- Environment variable tests
- Transport selection tests

✅ **Documentation**
- Enhanced README with absolute GitHub URLs for PyPI compatibility
- HTTP transport configuration guide
- Environment variables reference

### Changed

- Enhanced configuration system with CLI argument support
- Improved documentation for HTTP transport
- Better error messages for configuration issues

### Fixed

- Configuration precedence (CLI args > env vars > defaults)
- CORS header exposure for browser clients

---

## [0.2.6] - 2025-10-15

### Added

✅ **python-arango 8.2.2 Upgrade**
- Upgraded from python-arango 7.x to 8.2.2
- Support for latest ArangoDB features
- Improved performance and stability

✅ **Unified Index API**
- Migrated to unified `add_index()` API
- Replaced deprecated `add_hash_index()`, `add_skiplist_index()`, `add_persistent_index()`
- Backward-compatible index creation

### Changed

- Updated all index creation code to use `add_index()`
- Enhanced index management tools
- Improved index documentation

### Fixed

- Deprecation warnings from python-arango 7.x
- Index type handling for ArangoDB 3.11+

### Deprecated

- ⚠️ Old index creation methods (still supported but deprecated):
  - `add_hash_index()` → Use `add_index(type="hash")`
  - `add_skiplist_index()` → Use `add_index(type="skiplist")`
  - `add_persistent_index()` → Use `add_index(type="persistent")`

---

## [0.2.5] - 2025-10-10

### Added

✅ **HTTP Transport Phase 1: Core Implementation**
- Starlette-based HTTP transport
- StreamableHTTPSessionManager integration
- Health check endpoint (`/health`)
- CORS middleware with proper header exposure
- Stateful and stateless operation modes
- uvicorn ASGI server integration

✅ **Low-Level MCP Server API**
- Migrated from FastMCP to low-level Server API
- Custom lifespan management with retry logic
- Runtime state modification for lazy connection recovery
- Centralized tool dispatch via TOOL_REGISTRY

✅ **MCP SDK 1.18.0 Upgrade**
- Updated to MCP SDK 1.18.0
- StreamableHTTP transport support
- Enhanced session management

### Changed

- Server architecture to support multiple transports
- Entry point to handle transport selection (stdio or HTTP)
- Configuration system to support HTTP-specific settings

### Fixed

- Connection retry logic for Docker startup delays
- Graceful degradation when database unavailable

---

## [0.2.0-0.2.4] - 2025-09-01 to 2025-10-01

### Added

✅ **Tool Routing Refactor**
- Dictionary-based tool dispatch (O(1) lookup)
- `@register_tool()` decorator pattern
- Centralized tool registration via TOOL_REGISTRY
- Automatic duplicate detection

✅ **Advanced Graph Management**
- Graph backup and restore tools
- Graph analytics (statistics, vertex/edge counts)
- Named graph operations
- Graph traversal tools

✅ **Content Conversion System**
- JSON format conversion
- Markdown table generation
- YAML format support
- Table format for structured data

✅ **Enhanced Error Handling**
- `@handle_errors` decorator for consistent error formatting
- Detailed error context (tool name, error type)
- Centralized logging

### Changed

- Centralized tool registration (from if-elif chain to registry)
- Improved error handling and validation
- Enhanced tool documentation

### Fixed

- Tool dispatch performance (O(n) → O(1))
- Error message consistency
- Validation error handling

---

## [0.1.x] - 2025-08-01

### Added

✅ **Initial Release**
- Basic MCP tools for ArangoDB operations:
  - CRUD operations (create, read, update, delete)
  - AQL query execution
  - Collection management
  - Index management
  - Database operations
- stdio transport for desktop AI clients
- ArangoDB integration with python-arango 7.x
- Docker Compose setup
- PowerShell setup script for Windows

✅ **Core Features**
- 7 baseline tools for essential operations
- Pydantic validation for tool arguments
- Basic error handling
- Environment variable configuration

### Known Limitations

- stdio transport only (no HTTP support)
- Limited graph operations
- No content conversion
- Basic error messages

---

## Migration Guides

### 0.2.6 → 0.2.7

**No Breaking Changes** - Fully backward compatible

**New Features:**
- HTTP transport CLI arguments
- Environment variables for HTTP configuration
- Version bump script

**Recommended Actions:**
1. Update to 0.2.7: `pip install --upgrade mcp-arangodb-async`
2. Review new environment variables in [Environment Variables Reference](../configuration/environment-variables.md)
3. Try HTTP transport: `python -m mcp_arangodb_async --transport http`

---

### 0.2.5 → 0.2.6

**Breaking Changes:** None (backward compatible)

**API Changes:**
- ⚠️ Deprecated index methods (still work but show warnings):
  - `add_hash_index()` → Use `add_index(type="hash")`
  - `add_skiplist_index()` → Use `add_index(type="skiplist")`
  - `add_persistent_index()` → Use `add_index(type="persistent")`

**Migration Steps:**

**1. Update dependency:**
```bash
pip install --upgrade mcp-arangodb-async
```

**2. Update index creation code (optional but recommended):**

**Before (0.2.5):**
```python
# Using deprecated methods
collection.add_hash_index(fields=["email"], unique=True)
collection.add_skiplist_index(fields=["created_at"])
collection.add_persistent_index(fields=["user_id", "status"])
```

**After (0.2.6):**
```python
# Using unified add_index() API
collection.add_index(fields=["email"], type="hash", unique=True)
collection.add_index(fields=["created_at"], type="skiplist")
collection.add_index(fields=["user_id", "status"], type="persistent")
```

**3. Test your application:**
```bash
# Run tests to ensure compatibility
pytest tests/
```

**Note:** Old methods still work in 0.2.6 but will be removed in 1.0.0.

---

### 0.2.0-0.2.4 → 0.2.5

**Breaking Changes:** None (backward compatible)

**Major Changes:**
- HTTP transport added (stdio still default)
- Low-level MCP Server API (internal change, no API impact)
- MCP SDK 1.18.0 upgrade

**Migration Steps:**

**1. Update dependency:**
```bash
pip install --upgrade mcp-arangodb-async
```

**2. (Optional) Try HTTP transport:**

**Add to `.env`:**
```bash
MCP_TRANSPORT=http
MCP_HTTP_HOST=0.0.0.0
MCP_HTTP_PORT=8000
```

**Start server:**
```bash
python -m mcp_arangodb_async
```

**Test health endpoint:**
```bash
curl http://localhost:8000/health
```

**3. No code changes required** - stdio transport remains default

---

### 0.1.x → 0.2.x

**Breaking Changes:** None (backward compatible)

**Major Changes:**
- Tool routing refactor (internal change, no API impact)
- 27 new tools added (34 total)
- Graph management tools
- Content conversion system
- HTTP transport support (0.2.5+)

**Migration Steps:**

**1. Update dependency:**
```bash
pip install --upgrade mcp-arangodb-async
```

**2. Review new tools:**
- See [Tools Reference](../user-guide/tools-reference.md) for complete list
- New graph tools: `arango_graph_backup`, `arango_graph_restore`, `arango_graph_stats`
- New content tools: `arango_convert_to_json`, `arango_convert_to_markdown`, etc.

**3. Update configuration (if needed):**

**New environment variables (optional):**
```bash
# Connection tuning
ARANGO_CONNECT_RETRIES=3
ARANGO_CONNECT_DELAY_SEC=1.0
ARANGO_TIMEOUT_SEC=30.0

# Logging
LOG_LEVEL=INFO

# Toolset selection
MCP_COMPAT_TOOLSET=full  # or baseline
```

**4. Test your application:**
```bash
# Verify all tools available
python scripts/mcp_stdio_client.py

# Should show 34 tools (full toolset)
```

**5. No code changes required** - All existing tools work as before

---

## Versioning Policy

This project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR version** (X.0.0): Incompatible API changes
- **MINOR version** (0.X.0): New features, backward compatible
- **PATCH version** (0.0.X): Bug fixes, backward compatible

### Deprecation Policy

- Deprecated features are marked with ⚠️ warnings
- Deprecated features remain functional for at least 2 minor versions
- Deprecated features are removed in next major version

**Example:**
- Feature deprecated in 0.2.6
- Still works in 0.2.x and 0.3.x
- Removed in 1.0.0

---

## Upgrade Recommendations

### For End Users

**Stay on latest MINOR version:**
- ✅ New features
- ✅ Bug fixes
- ✅ Security updates
- ✅ Backward compatible

**Example:** 0.2.5 → 0.2.7 (safe upgrade)

---

### For Developers

**Test before upgrading MAJOR versions:**
- ⚠️ May contain breaking changes
- ⚠️ Review migration guide
- ⚠️ Update code if needed
- ⚠️ Run full test suite

**Example:** 0.2.7 → 1.0.0 (test thoroughly)

---

## Related Documentation

- [Installation Guide](../getting-started/installation.md)
- [Environment Variables](../configuration/environment-variables.md)
- [HTTP Transport](http-transport.md)
- [Tools Reference](../user-guide/tools-reference.md)

