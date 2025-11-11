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

1. [Version 0.4.0 (Current)](#version-040---2025-11-11)
2. [Version 0.3.2](#version-032---2025-10-20)
3. [Version 0.3.1](#version-031---2025-10-20)
4. [Version 0.3.0](#version-030---2025-10-20)
5. [Version 0.2.11](#version-0211---2025-10-20)
6. [Version 0.2.10](#version-0210---2025-10-20)
7. [Version 0.2.9](#version-029---2025-10-20)
8. [Version 0.2.8](#version-028---2025-10-20)
9. [Version 0.2.7](#version-027---2025-10-19)
10. [Version 0.2.6](#version-026---2025-10-15)
11. [Version 0.2.5](#version-025---2025-10-10)
12. [Version 0.2.0-0.2.4](#version-020-024---2025-09-01-to-2025-10-01)
13. [Version 0.1.x](#version-01x---2025-08-01)
14. [Migration Guides](#migration-guides)

---

## [0.4.0] - 2025-11-11

**Current Release**

### Added

✅ **MCP Design Pattern Tools (9 new tools)**
- **Progressive Tool Discovery (2 tools):**
  - `arango_search_tools` - Search for tools by keywords and categories with configurable detail levels
  - `arango_list_tools_by_category` - List tools organized by category for workflow-specific discovery
  - Enables on-demand tool loading instead of loading all 43 tools upfront
  - Achieves 95-98% token savings in initial context window

- **Context Switching (3 tools):**
  - `arango_switch_context` - Switch between 6 predefined workflow contexts (baseline, data_analysis, graph_modeling, bulk_operations, schema_validation, full)
  - `arango_get_active_context` - Get currently active workflow context
  - `arango_list_contexts` - List all available workflow contexts with descriptions
  - Enables workflow-specific tool sets for focused operations

- **Tool Unloading (4 tools):**
  - `arango_advance_workflow_stage` - Advance through 4 workflow stages (setup, data_loading, analysis, cleanup)
  - `arango_get_tool_usage_stats` - Get usage statistics for all tools
  - `arango_unload_tools` - Manually unload specific tools from active context
  - `arango_graph_traversal` - Alias for arango_traverse (backward compatibility)
  - Enables automatic tool lifecycle management across workflow stages

✅ **Comprehensive MCP Design Patterns Documentation**
- **New Guide:** `docs/user-guide/mcp-design-patterns.md` (925 lines)
  - Complete documentation for all three MCP design patterns
  - Workflow examples demonstrating up to 98.7% token savings
  - Decision matrix for pattern selection
  - Best practices and error handling guidance
  - Real-world use cases and implementation examples

- **Updated Tools Reference:** `docs/user-guide/tools-reference.md`
  - Added section 11: MCP Design Pattern Tools (9 tools)
  - Complete API documentation with parameters, returns, examples, use cases, and best practices
  - Updated tool count from 34 to 43 tools throughout documentation

- **Updated Main Documentation:**
  - `README.md` - Added MCP Design Patterns feature highlight and quick link
  - `docs/README.md` - Added MCP Design Patterns Guide to learning paths
  - Updated architecture diagram to reflect 43 tools

✅ **Manual Validation Test Suite**
- **New Test File:** `tests/test_mcp_design_patterns_manual.py` (366 lines)
  - Comprehensive validation tests for all three MCP design pattern workflows
  - 22 validation scenarios covering all 9 tools
  - Tests connect to actual ArangoDB instance and exercise tools through MCP server
  - Validates Progressive Tool Discovery (5 scenarios)
  - Validates Context Switching (8 scenarios)
  - Validates Tool Unloading (9 scenarios)

✅ **Version Management Script**
- **New Script:** `scripts/bvn.py` (Bump Version Number) - 300 lines
  - Automated version management with semantic versioning validation
  - Commands: `--version "X.Y.Z"`, `--pypi true/false`, `--dry-run`
  - Validates new version is semantically greater than current version
  - Updates version in `pyproject.toml`
  - Manages `publish_on_pypi` flag for PyPI publication workflow
  - Dry-run mode for previewing changes without applying
  - Comprehensive error handling and clear success/error messages

### Changed

- **Tool Count:** Increased from 34 to 43 tools (9 new MCP Design Pattern tools)
- **Tool Categories:** Expanded from 9 to 10 categories (added MCP Design Pattern Tools)
- **Documentation:** 1,455 lines added across 4 documentation files
- **Project Structure:** Test files properly organized in `tests/` directory
- **Version:** Bumped from 0.3.2 to 0.4.0 (MINOR version increment for new features)

### Technical Details

- **MCP Design Patterns Implementation:**
  - Tool registry with category-based organization
  - Context management with workflow-specific tool sets
  - Tool lifecycle tracking with usage statistics
  - Backward compatibility maintained with tool aliases

- **Documentation Standards:**
  - Follows pedagogical approach (Context→Concept→Code→Conclusion)
  - Consistent formatting with existing documentation style
  - Absolute GitHub URLs for PyPI compatibility
  - Cross-references validated throughout

- **Testing Approach:**
  - Manual validation tests complement existing unit/integration tests
  - Tests exercise actual MCP server and ArangoDB connection
  - Validates end-to-end workflow behavior
  - 100% pass rate (22/22 validation tests)

### Performance Impact

- **Token Savings:** Up to 98.7% reduction in initial context window through progressive tool discovery
- **Workflow Efficiency:** Context-specific tool sets reduce cognitive load and improve focus
- **Tool Management:** Automatic lifecycle management reduces manual tool selection overhead

---

## [0.3.2] - 2025-10-20

### Fixed

✅ **Test Suite Stability (20 failing tests resolved)**
- Fixed handler invocation logic using signature inspection instead of try/catch approach
- Resolved mock object setup issues across multiple test files to return proper iterable data structures
- Added missing `tabulate` dependency to development requirements
- Updated test environment detection in backup.py for secure path validation while allowing test execution
- Fixed schema property assertions to match Pydantic v2 camelCase generation
- Corrected function signature mismatches in handler unit tests for new graph statistics parameters
- Improved integration test mocking by replacing fragile patches with robust mock database setups
- Added missing imports (`ANY`, `mock_open`) to test files

✅ **Graph Management Robustness**
- Enhanced parameter handling consistency across all 5 graph management tools
- Improved error recovery and validation for graph backup/restore operations
- Standardized mock database structures for reliable integration testing
- Fixed database unavailable error handling in integration tests

### Changed

- **Test Results:** Improved from 208 passing tests (87% pass rate) to 228 passing tests (99.1% pass rate)
- **Graph Tools:** All 5 graph management tools (`arango_backup_graph`, `arango_restore_graph`, `arango_backup_named_graphs`, `arango_validate_graph_integrity`, `arango_graph_statistics`) now working reliably
- **CI/CD Confidence:** Stable test suite enables reliable continuous integration

### Technical Details

- Handler invocation now uses `inspect.signature()` to detect `VAR_KEYWORD` parameters
- Test environment detection prevents path traversal security issues while allowing test execution
- Mock objects properly configured with iterable return values and realistic data structures
- Integration tests use comprehensive mock database setup instead of fragile handler patches

---

## [0.3.1] - 2025-10-20

### Added

✅ **Enhanced README Configuration Examples**
- Updated Claude Desktop configuration with `server` subcommand
- Improved environment variable examples with secure defaults
- Changed default credentials from `root/changeme` to `mcp_arangodb_user/mcp_arangodb_password`
- Better formatting and readability in Quick Start section

### Changed

- README.md formatting improvements with better spacing
- Enhanced configuration examples for better security practices

### Fixed

- GitHub branch references corrected from `main` to `master` in all absolute URLs
- Ensures PyPI documentation links work correctly

---

## [0.3.0] - 2025-10-20

### Added

✅ **Comprehensive Pedagogical Documentation (14 files)**
- Complete documentation overhaul following pedagogical approach (Context→Concept→Code→Conclusion)
- **Getting Started Guides:**
  - Installation guide with ArangoDB licensing information
  - Quick Start guide for stdio transport (Claude Desktop, Augment Code)
  - First Interaction guide with test prompts and examples
- **User Guides:**
  - Complete tools reference (34 tools across 9 categories)
  - Enhanced troubleshooting guide with common issues and solutions
- **Configuration Guides:**
  - Transport configuration (stdio and HTTP)
  - Complete environment variables reference
- **Developer Guides:**
  - Architecture overview with system design
  - Low-level MCP rationale (why not FastMCP)
  - HTTP transport implementation guide
  - This changelog document
- **Examples:**
  - Sophisticated codebase dependency analysis example
  - Graph modeling for software architecture
  - Dependency analysis and circular detection
  - Impact analysis and complexity scoring
- **Navigation:**
  - Documentation hub (docs/README.md) with learning paths
  - Style guide for documentation consistency

✅ **Enhanced Root README**
- Absolute GitHub URLs for PyPI compatibility
- Quick links section with direct documentation access
- Comprehensive features overview
- Installation guides for both PyPI and Docker
- Quick Start for stdio and HTTP transports
- Configuration reference with environment variables
- All 34 tools overview in 9 categories
- Use case example (Codebase Graph Analysis)
- Complete documentation links
- Troubleshooting section
- License information

### Changed

- Documentation structure completely reorganized for better discoverability
- All documentation follows pedagogical approach with progressive disclosure
- README.md optimized to 382 lines with maximum actionability
- Internal documentation uses relative links for maintainability
- Root README uses absolute GitHub URLs for PyPI compatibility

### Documentation Structure

```
docs/
├── README.md - Navigation hub with learning paths
├── STYLE_GUIDE.md - Documentation standards
├── getting-started/
│   ├── installation.md
│   ├── quickstart-stdio.md
│   └── first-interaction.md
├── user-guide/
│   ├── tools-reference.md
│   └── troubleshooting.md
├── configuration/
│   ├── transport-configuration.md
│   └── environment-variables.md
├── developer-guide/
│   ├── architecture.md
│   ├── low-level-mcp-rationale.md
│   ├── http-transport.md
│   └── changelog.md
└── examples/
    └── codebase-analysis.md
```

**Total Documentation:** ~2,679 lines across 14 files

---

## [0.2.11] - 2025-10-20

### Added

✅ **Phase 4: Polish & Examples**
- **Sophisticated Codebase Analysis Example:**
  - Complete graph modeling example for software dependency analysis
  - Problem statement addressing traditional tools limitations
  - Graph model design with 3 vertex collections and 3 edge collections
  - Step-by-step implementation guide with Claude prompts
  - 5 analysis queries: direct dependencies, transitive dependencies, reverse dependencies, circular detection, leaf modules
  - 3 advanced use cases: dependency depth analysis, call chain analysis, complexity scoring
  - Real-world AQL query examples with expected results
  - Pedagogical approach (Context→Concept→Code→Conclusion)

### Changed

- **README.md Enhanced:**
  - Added link to codebase-analysis.md example
  - Added "Examples" section to documentation links
  - Optimized to 382 lines (within 400-500 target)
  - All 30 absolute GitHub URLs verified for PyPI compatibility
- **docs/README.md Updated:**
  - Added "Examples" section with codebase-analysis.md
  - Updated Learning Path 1 to include example
  - Cross-references validated, relative links maintained

### Documentation Review

✅ Grammar and formatting validated across all Phase 1-4 files
✅ Cross-references validated (absolute URLs in README.md, relative in docs/)
✅ Link validation completed (30 absolute GitHub URLs, all relative links)
✅ Consistency check passed across all documentation

**Phase 4 Complete:** All deliverables match PEDAGOGICAL_DOCUMENTATION_ROADMAP.md specifications

---

## [0.2.10] - 2025-10-20

### Added

✅ **Phases 1-3 Comprehensive Documentation (8 files)**
- **Phase 1 - Foundation:**
  - Enhanced README.md (379 lines) with absolute GitHub URLs for PyPI compatibility
  - Quick links, features overview, architecture diagram
  - Installation guides for stdio and HTTP transports
  - Configuration reference, tools overview, troubleshooting
- **Phase 2 - Architecture & Rationale (4 files):**
  - Low-level MCP rationale (300 lines) - Why not FastMCP
  - Environment variables reference (300 lines) - Complete configuration guide
  - Troubleshooting guide (300 lines) - Common issues and solutions
  - Architecture overview (300 lines) - System design with 7-layer diagram
- **Phase 3 - Advanced Features & History (3 files):**
  - HTTP transport guide (300 lines) - Starlette integration, deployment
  - Changelog (300 lines) - Version history and migration guides
  - Documentation hub (300 lines) - Navigation with learning paths

### Changed

- Documentation structure completely reorganized for better discoverability
- All documentation follows pedagogical approach (Context→Concept→Code→Conclusion)
- Internal documentation uses relative links for maintainability
- Root README uses absolute GitHub URLs for PyPI compatibility

### Removed

- Deleted 5 incorrect files that deviated from roadmap:
  - docs/architecture/design-decisions.md
  - docs/architecture/transport-comparison.md
  - docs/developer-guide/contributing.md
  - docs/developer-guide/testing.md
  - docs/developer-guide/extending-tools.md

**Phases 1-3 Complete:** 8/8 deliverables (1 + 4 + 3 files)

---

## [0.2.9] - 2025-10-20

### Added

✅ **Phase 2: Architecture and Configuration Documentation (3 files)**
- **Design Decisions Documentation (731 lines):**
  - Low-level MCP Server API rationale vs FastMCP
  - Docker rationale with persistent data configuration
  - Retry/reconnect logic with graceful degradation
  - Tool registration pattern evolution (if-elif → decorator)
  - Centralized error handling strategy
- **Transport Comparison Guide (614 lines):**
  - stdio vs HTTP transport comparison with architecture diagrams
  - Technical comparison tables (protocol, deployment, scalability, security)
  - 4 real-world use case recommendations
  - Performance benchmarks (stdio: 0.8ms, HTTP: 2.3ms latency)
  - Security implications and best practices
  - Migration guide (stdio ↔ HTTP)
- **Transport Configuration Guide (732 lines):**
  - Complete stdio transport configuration (Claude Desktop, Augment Code)
  - HTTP transport configuration (Docker, Kubernetes)
  - Environment variables reference with examples
  - Client-specific integration guides (JavaScript, Python)
  - Troubleshooting guide for common transport issues

### Documentation Features

- Pedagogical-first approach (Context→Concept→Code→Conclusion)
- Production-ready examples (Docker Compose, Kubernetes deployments)
- Security best practices (TLS, CORS, authentication, firewall)
- Real-world use cases (local dev, web apps, K8s, CI/CD)
- Comprehensive troubleshooting sections

**Phase 2 Complete:** 3/3 deliverables

---

## [0.2.8] - 2025-10-20

### Added

✅ **Phase 1: Foundation Documentation (4 files)**
- **Quick Start Guide (300 lines):**
  - Complete stdio quickstart with step-by-step instructions
  - MCP client configuration for Claude Desktop and Augment Code
  - Health check verification and troubleshooting
- **First Interaction Guide (300 lines):**
  - Basic verification tests for server connectivity
  - 5 AI-Coding use cases adapted to software engineering workflows
  - Advanced tests for bulk operations and indexing
- **Installation Guide (300 lines):**
  - Complete installation guide with Docker setup
  - ArangoDB 3.11 licensing details (Apache 2.0 vs BUSL-1.1)
  - Database initialization and environment configuration
  - Comprehensive troubleshooting section
- **Tools Reference (994 lines):**
  - Complete documentation for all 34 MCP tools
  - Organized into 9 categories with examples
  - Parameters, return values, use cases, and best practices
  - Toolset configuration guide (baseline vs full)

### Documentation Features

- Pedagogical-first approach (teaches, not just informs)
- AI-Coding context examples (codebase analysis, API evolution, etc.)
- Progressive complexity (beginner → intermediate → advanced)
- Style guide compliant (relative links, proper formatting)
- Actionable content (users can immediately apply knowledge)

**Phase 1 Complete:** 4/5 deliverables (README.md transformation pending)

---

## [0.2.7] - 2025-10-19

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

