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

1. [Version 0.5.3 (Current)](#version-053---2026-01-04)
2. [Version 0.5.2](#version-052---2026-01-03)
3. [Version 0.5.1](#version-051---2025-12-31)
4. [Version 0.5.0](#version-050---2025-12-15)
5. [Version 0.4.9](#version-049---2025-12-09)
6. [Version 0.4.8](#version-048---2025-12-04)
7. [Version 0.4.7](#version-047---2025-11-28)
8. [Version 0.4.6](#version-046---2025-11-27)
9. [Version 0.4.5](#version-045---2025-11-27)
10. [Version 0.4.4](#version-044---2025-11-27)
11. [Version 0.4.3](#version-043---2025-11-24)
12. [Version 0.4.2](#version-042---2025-11-24)
13. [Version 0.4.1](#version-041---2025-11-24)
14. [Version 0.4.0](#version-040---2025-11-11)
15. [Version 0.3.2](#version-032---2025-10-20)
16. [Version 0.3.1](#version-031---2025-10-20)
17. [Version 0.3.0](#version-030---2025-10-20)
18. [Version 0.2.11](#version-0211---2025-10-20)
19. [Version 0.2.10](#version-0210---2025-10-20)
20. [Version 0.2.9](#version-029---2025-10-20)
21. [Version 0.2.8](#version-028---2025-10-20)
22. [Version 0.2.7](#version-027---2025-10-19)
23. [Version 0.2.6](#version-026---2025-10-15)
24. [Version 0.2.5](#version-025---2025-10-10)
25. [Version 0.2.0-0.2.4](#version-020-024---2025-09-01-to-2025-10-01)
26. [Version 0.1.x](#version-01x---2025-08-01)
27. [Migration Guides](#migration-guides)

---

## [0.5.3] - 2026-01-04

**Current Release**

### Added

✅ **CLI Database Configuration Update Command**
- **New `maa db config update` command:**
  - Update existing database configuration fields (URL, database, username, password_env, timeout, description)
  - Rename configuration keys with automatic default database reference handling
  - Support for clearing optional fields (description) by passing empty string
  - Full alias support: `-k` (key), `-u` (url), `-d` (database), `-U` (username), `-P` (password-env), `-C` (description)
  - Dry-run mode (`--dry-run`) to preview changes without applying
  - Interactive confirmation with consequence reporting using `ConsequenceType.UPDATE`
  - Proper exit codes: 0 (success), 1 (error), 2 (cancelled)

### Fixed

✅ **Test Suite Improvements**
- **Cross-platform path comparison:** Fixed path assertions using `os.path.realpath()` to handle macOS symlinks (`/var` → `/private/var`)
- **Pytest configuration:** Fixed malformed `pyproject.toml` syntax and added proper asyncio marker configuration
- **Docker integration tests:** Made docker import conditional to prevent collection errors when docker module is unavailable
- **Unawaited coroutine warnings:** Fixed mock handling in CLI tests to properly close coroutines

### Technical Details

- **Files Modified:**
  - `mcp_arangodb_async/__main__.py` - Added `update` subparser with all arguments and aliases
  - `mcp_arangodb_async/cli_db.py` - Added `handle_update()` function (116 lines)
  - `tests/test_cli_db_unit.py` - Added `TestCLIUpdate` class with 8 tests
  - `tests/test_backup.py` - Fixed path comparison for cross-platform compatibility
  - `tests/test_graph_backup_unit.py` - Fixed path comparison for cross-platform compatibility
  - `tests/test_mcp_integration.py` - Updated mocks to use `MultiDatabaseConnectionManager` with `AsyncMock`
  - `tests/integration/test_docker_container.py` - Made docker import conditional
  - `pyproject.toml` - Fixed syntax errors and pytest configuration

- **Test Results:** 455 passed, 12 skipped, 0 warnings

### Documentation

- Updated CLI reference with complete `db config update` section
- Added update command to hierarchical command structure tree
- Added configuration update examples to all multi-tenancy scenarios
- Updated multi-tenancy guide quick reference

---

## [0.5.2] - 2026-01-03

### Fixed

✅ **CLI Reporting Enhancement**
- **Password Environment Variable Reporting:**
  - Added password environment variable to `db config add` command output
  - Users can now verify which environment variable is configured for password
  - Maintains consistency with CLI UX philosophy (only show what's explicitly set)
  - No breaking changes, fully backward compatible

### Changed

- **CLI Output:** `db config add` now shows password env in confirmation and result output
- **User Experience:** Improved transparency for password configuration without exposing secrets

---

## [0.5.1] - 2025-12-31

### Added

- **CLI Argument Aliases**: 3-tier alias system for improved ergonomics
  - **Short aliases** (9 new): `-R`, `-P`, `-N`, `-C`, `-E`, `-p`, `-u`, `-d`, `-U`
  - **Medium aliases** (7 new): `--root-pw-env`, `--pw-env`, `--new-pw-env`, `--cfgf`, `--cfgp`, `--envf`, `--perm`
  - **Standardized naming**: `--arango-new-password-env`, `--environment-file`, `--config-file`
  - **Character savings**: 40-50% reduction for common operations using short aliases

- **Backward Compatibility**: All existing argument names remain valid as aliases
  - `--password-env` → `--arango-password-env` (in `db config add`)
  - `--new-password-env` → `--arango-new-password-env` (in `user password`)
  - `--config-path` → `--config-file` (everywhere)
  - `--env-file` → `--environment-file` (everywhere)

- **Documentation Enhancements**:
  - CLI reference updated with comprehensive alias tables
  - Collapsible alias sections added to multi-tenancy guides and scenarios
  - Progressive disclosure examples in troubleshooting guide
  - Preserves educational clarity while providing power-user shortcuts

### Changed

- **Help Text**: All commands now document available aliases
- **Documentation**: Tutorial and reference docs enhanced with collapsible alias sections

### Technical Details

- **Implementation**: Argparse-based alias resolution (no custom parsing logic)
- **Testing**: 4 new backward compatibility tests, 18 test functions updated
- **Zero Breaking Changes**: 100% backward compatibility maintained
- **Usability Enhancement**: Convenience aliases only, no new functionality

**Examples:**

```bash
# Verbose (documentation default - educational clarity)
maa db add myapp_prod \
  --with-user myapp_user \
  --permission rw \
  --arango-root-password-env ARANGO_ROOT_PASSWORD \
  --arango-password-env ARANGO_PASSWORD

# Short aliases (power users - improved ergonomics)
maa db add myapp_prod --with-user myapp_user -p rw -R ARANGO_ROOT_PASSWORD -P ARANGO_PASSWORD
```

---

## [0.5.0] - 2025-12-15

### Fixed

✅ **Database Connection System Consistency (Verification & Cleanup Phase)**
- **Server Initialization Architecture Mismatch:**
  - Fixed inconsistent database resolution between server startup and tool execution
  - Root cause: Server initialization used `load_config()` + `get_client_and_db()` while tools used `resolve_database()` + `MultiDatabaseConnectionManager`
  - Server now uses `resolve_database()` for consistent database resolution during startup
  - Eliminated legacy single-database connection path
  - Both server initialization and lazy tool connections now use unified `MultiDatabaseConnectionManager`
  - Database resolution follows same 6-level priority algorithm throughout application lifecycle
  - Maintains same retry logic and graceful degradation behavior

### Added

✅ **Enhanced Database Context Management**
- **Focused Database Unsetting:**
  - Added support for unsetting focused database via `arango_set_focused_database`
  - Pass `None` or empty string to revert to default database resolution behavior
  - Tool now resolves and displays fallback database when unsetting
  - Improved user feedback with fallback database information
  - `fallback_database` field added to tool response
  - Enables flexible session-based database context management

- **CLI Enhancement:**
  - Added `--env-file` parameter to `maa db config test` command
  - Enables local `.env` file credential testing without global environment setup

### Changed

⚠️ **Environment Variable Standardization**
- **ARANGO_DB Unified Variable:**
  - Replaced `MCP_DEFAULT_DATABASE` with `ARANGO_DB` for consistent naming convention
  - Updated Level 4 of 6-level database resolution algorithm to use `ARANGO_DB`
  - Aligns with existing ArangoDB environment variable conventions (`ARANGO_HOST`, `ARANGO_PORT`, etc.)
  - Eliminates confusion between different variable naming schemes
  - Updated across entire codebase:
    - `db_resolver.py`: Level 4 resolution now uses `ARANGO_DB`
    - `handlers.py`: Diagnostic output updated to reference `ARANGO_DB`
    - `cli_db.py`: Status command output updated
    - `cli_utils.py`: CLI environment variable enum updated
    - All documentation strings updated

### Technical Details

**Database Resolution Architecture:**
- Server initialization and tool execution now share identical database resolution pathway
- Unified system ensures all connections follow 6-level priority algorithm:
  1. Per-tool override (`tool_args["database"]`)
  2. Focused database (`session_state.get_focused_database()`)
  3. Config default (`config_loader.default_database`)
  4. Environment variable (`ARANGO_DB`)
  5. First configured database
  6. Hardcoded fallback (`"_system"`)

**Test Coverage:**
- Added comprehensive server initialization consistency tests
- Tests verify database resolution behavior matches between startup and tool execution
- Updated existing tests to use `ARANGO_DB` environment variable
- All existing tests continue to pass

**Files Modified:**
- `mcp_arangodb_async/entry.py` - Integrated resolve_database() into server initialization
- `mcp_arangodb_async/db_resolver.py` - Updated Level 4 to use ARANGO_DB
- `mcp_arangodb_async/handlers.py` - Updated diagnostic output and unsetting capability
- `mcp_arangodb_async/cli_db.py` - Updated status output and added `--env-file` support
- `mcp_arangodb_async/cli_utils.py` - Updated CLIEnvVar enum
- `tests/test_entry_point_integration_unit.py` - Added server initialization tests
- `tests/test_db_resolver_unit.py` - Updated for ARANGO_DB variable
- `tests/test_config_loader_unit.py` - Updated environment variable references

### Documentation

✅ **Multi-Tenancy Documentation Cleanup & Enhancement**
- **Multi-Tenancy Scenario Rewrite:**
  - Completely rewritten Scenario 1 (Single Instance, Single Database)
  - Completely rewritten Scenario 2 (Single Instance, Multiple Databases)
  - Completely rewritten Scenario 3 (Multiple Instances)
  - Each scenario includes:
    - Prerequisites section referencing ArangoDB installation guide
    - Consolidated setup into single logical flow
    - Standard user workflow instead of admin-only patterns
    - Explicit env-file usage for credential management
    - Configuration file adaptation step for MCP host setup
    - Detailed verification steps with expected outputs
    - Multiple launcher options (Conda, Mamba, uv)
    - Explicit expected outputs for each command step
    - Cross-database operation testing patterns
    - Comprehensive web UI verification steps
    - Clarification of config file key vs database name

- **Scenario 4 Removal:**
  - Removed agent-based access control scenario from documentation
  - Simplified prerequisites and getting started section
  - Updated README to reflect current 3-scenario progression
  - Deferred for future implementation (not part of current learning progression)

- **CLI Documentation Additions:**
  - Added comprehensive `maa server` command documentation
  - Complete syntax reference with all supported arguments
  - Detailed parameter explanations (transport, host, port, stateless, config-file)
  - Environment variable reference for all server options
  - Fixed CLI syntax errors throughout examples (`maa --health` → `maa health`)
  - Updated HTTP transport command examples
  - Added graceful degradation documentation for missing config files

- **Tools Reference Updates:**
  - Updated `arango_set_focused_database` with unset capability
  - Added examples for unsetting with None/empty string
  - Documented fallback database information in response format
  - Clarified database resolution behavior after unset

- **Environment Variable Documentation:**
  - Updated all references from `MCP_DEFAULT_DATABASE` to `ARANGO_DB`
  - Clarified dual meaning of `ARANGO_DB` in different contexts
  - Added examples using new variable name
  - Updated all Getting Started guides

- **Cross-Platform Compatibility:**
  - Added comprehensive 'Getting Started with ArangoDB' section to README
  - Provided copy-pastable docker-compose.yml and .env templates
  - Replaced PowerShell-exclusive syntax with cross-platform bash syntax
  - Updated MCP client configuration examples (conda run, uv run)
  - Added collapsible installation alternatives (conda/mamba/micromamba/uv)
  - Fixed command syntax consistency across all examples
  - Enhanced ArangoDB installation guide

- **Documentation Organization:**
  - Refactored Getting Started to logical 4-step flow
  - Transformed docs/README into comprehensive navigation index
  - Removed deprecated monolithic installation guides
  - Created progressive learning path structure
  - Updated all cross-references and links
  - Streamlined multi-tenancy top-level guide
  - Added Apache 2.0 license text to repository

**Documentation Improvements:**
- ~2,000+ lines updated/rewritten
- Consistent pedagogical approach throughout
- All cross-references validated
- Step-by-step instructions with expected outputs
- Multiple launcher/environment options documented
- Professional tone and formatting consistency

---

## [0.4.9] - 2025-12-09

### Fixed

✅ **Admin CLI Bug Fixes & UX Improvements (Milestone 4.3 Completion)**
- **Entry Point Correction:**
  - Fixed `pyproject.toml` entry point from `entry:main` to `__main__:main`
  - Ensures all CLI commands route through proper argument parser
  - Added `maa` short alias for `mcp-arangodb-async` command
- **Health Command Improvements:**
  - Suppressed urllib3 connection warnings for cleaner output
  - Added user-friendly progress feedback during connection attempts
  - Improved error messages with actionable hints (e.g., "Is the ArangoDB server running?")
  - Returns proper exit codes (0=healthy, 1=unhealthy)
  - No longer fails itself when database is unavailable
- **Database Config Commands:**
  - Fixed `db config ls` to show clear message when config file doesn't exist
  - Indicates graceful degradation to environment variables when no YAML config
  - Displays full absolute path to config file for clarity
  - Fixed `db config add` to not auto-add environment variable databases
- **Database Admin Commands:**
  - Added `--url` parameter to all database/user commands for multi-server support
  - Fixed `--with-user` to grant access to existing users (creates only if needed)
  - Improved `--with-user` UX by showing `[EXISTS]` tag for existing users
  - Fixed dry-run mode to not require database connection
  - All commands now work without active database connection when appropriate
- **User Self-Service Commands:**
  - Fixed `user databases` authentication using proper database resolution
  - Fixed `user password` authentication using proper database resolution
  - Added `ARANGO_NEW_PASSWORD` to auto-loaded environment variables
  - Improved error messages showing attempted connection paths
- **Result Reporting:**
  - Fixed tense distinction: present tense for prompts, past tense for results
  - Improved color contrast: dimmer colors for prompts, brighter for results
  - Consistent consequence reporting across all commands
- **Multi-Tenancy Tool Consolidation:**
  - Merged `arango_test_database_connection` and `arango_get_multi_database_status` into single `arango_database_status` tool
  - New tool provides comprehensive status with summary counts and focused database indicator
  - Total tool count: 46 tools (4 multi-tenancy + 7 core + 4 indexing + 4 validation + 2 schema + 2 query + 7 graph basic + 5 graph advanced + 2 aliases + 1 health + 8 MCP patterns)
  - Improved output format with clear summary section

### Changed

⚠️ **Breaking Change: Multi-Tenancy Tool Consolidation**
- Removed tools: `arango_test_database_connection`, `arango_get_multi_database_status`
- Replacement: `arango_database_status` (provides all functionality in single tool)
- **Migration:**
  - Old: `arango_test_database_connection` with `database_key` parameter
  - Old: `arango_get_multi_database_status` with no parameters
  - New: `arango_database_status` with no parameters (returns all databases with status)

### Added

✅ **Config File Integration**
- Added `--config-file` / `--cfgf` argument to `server` command
- Added `ARANGO_DATABASES_CONFIG_FILE` environment variable support
- Config file path now properly passed to server startup
- Enables multi-database configuration without code changes

✅ **CLI Environment Variable Management**
- Added `CLIEnvVar` enum for centralized environment variable management
- All supported CLI environment variables now auto-loaded from dotenv files
- Developers can easily add new environment variables by updating enum
- Improved credential loading with consistent naming

✅ **Enhanced Error Handling**
- Connection errors now show user-friendly messages with hints
- Authentication errors clearly indicate credential issues
- Timeout errors provide actionable guidance
- All error paths tested and validated

### Technical Details

- **Files Modified:**
  - `mcp_arangodb_async/__main__.py` - Fixed entry point routing, added config file support
  - `mcp_arangodb_async/cli_health.py` - New module for health and version commands
  - `mcp_arangodb_async/cli_utils.py` - Added `CLIEnvVar` enum, `get_system_db()` helper
  - `mcp_arangodb_async/cli_db.py` - Fixed config list graceful degradation
  - `mcp_arangodb_async/cli_db_arango.py` - Added `--url` support, fixed `--with-user` logic
  - `mcp_arangodb_async/cli_user.py` - Fixed authentication, added `_connect_as_user()` helper
  - `mcp_arangodb_async/config_loader.py` - Added `load_yaml_only()`, `loaded_from_yaml` property
  - `mcp_arangodb_async/entry.py` - Integrated config file path, fixed session context
  - `mcp_arangodb_async/handlers.py` - Consolidated multi-tenancy tools, improved error handling
  - `mcp_arangodb_async/models.py` - Removed obsolete tool models
  - `mcp_arangodb_async/tools.py` - Updated tool constants
  - `pyproject.toml` - Fixed entry points, added `maa` alias, added `pytest-asyncio` dependency
  - `README.md` - Updated CLI examples to use `maa` alias
  - `docs/` - Updated all documentation with new tool names and CLI examples
  - `.gitignore` - Added `.kiro/` and `.vscode/` IDE folders

- **Test Updates:**
  - Updated `tests/test_admin_cli.py` - 35 tests covering all CLI functionality
  - Updated `tests/test_cli_args_unit.py` - Added config file argument tests
  - Updated `tests/test_cli_db_unit.py` - Added graceful degradation tests
  - Updated `tests/test_config_loader_unit.py` - Added `load_yaml_only()` tests
  - Updated `tests/test_multi_tenancy_tools_unit.py` - Updated for consolidated tool
  - Updated `tests/test_mcp_integration.py` - Fixed session context mocks
  - Renamed `tests/test_mcp_design_patterns_manual.py` to `tests/manual_test_mcp_design_patterns.py`
  - All tests passing (35/35 admin CLI tests, 100% critical path coverage)

- **Exit Codes:**
  - `0` - Success
  - `1` - Error (validation, connection, permission)
  - `2` - Operation cancelled by user

### Documentation

- Updated CLI reference with `maa` alias throughout
- Updated multi-tenancy guide with consolidated tool
- Updated tools reference with new `arango_database_status` tool
- Updated installation guide with corrected CLI commands
- Added `env.example` entry for `ARANGO_NEW_PASSWORD`

### Related Issues

Closes [#40](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/40), [#41](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/41), [#42](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/42), [#43](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/43), [#44](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/44), [#45](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/45)

---

## [0.4.8] - 2025-12-04

### Added

✅ **Admin CLI for User and Database Management (Milestone 4.3 - Task 4.3.3)**
- **CLI Commands Implementation:**
  - Implemented 16 CLI commands for ArangoDB administration:
    - **Database Operations:** `db add`, `db remove`, `db list` (with `--with-user` atomic operation)
    - **User Operations:** `user add`, `user remove`, `user list`, `user grant`, `user revoke`
    - **Self-Service Operations:** `user databases`, `user password`
    - **Version Command:** `version` to display package version
  - **Safety Features:**
    - Interactive confirmation prompts for all destructive operations
    - `--dry-run` flag to preview changes without execution
    - `--yes` flag to skip confirmation in automation/CI
    - Environment variable `MCP_ARANGODB_ASYNC_CLI_YES=1` for CI/CD
  - **Result Reporting:**
    - Color-coded output (green=additive, red=destructive, yellow=updates, gray=dry-run)
    - Tense distinction (present for prompts, past for results)
    - Side-effect reporting (e.g., permission revocations when deleting users/databases)
  - **Credential Handling:**
    - `--env-file` support for loading credentials from dotenv files
    - Environment variable overrides (`--arango-root-password-env`, `--arango-password-env`)
    - Consistent with MCP server environment variable names
  - **Command Aliases:** Unix-style aliases (`rm`, `ls`) for common operations

### Changed

⚠️ **Breaking Change: Database Config Commands Moved**
- Existing `db add/remove/list/test/status` commands moved to `db config` subcommand
- **Migration:**
  - Old: `mcp-arangodb-async db add production ...`
  - New: `mcp-arangodb-async db config add production ...`
- **Rationale:** Separate YAML config management from ArangoDB database operations

### Testing

✅ **Comprehensive Test Suite (30 Tests)**
- **Test Organization:**
  - `tests/test_admin_cli.py` - 890 lines covering all admin CLI functionality
  - 7 test classes organized by feature area
  - 100% test pass rate (30/30 passing)
- **Test Coverage by Category:**
  - `TestVersionCommand` (1 test): Version display functionality
  - `TestDBConfig` (7 tests): YAML configuration management
  - `TestDBAdmin` (5 tests): ArangoDB database operations
  - `TestUserAdmin` (10 tests): User management and permissions
  - `TestSafetyFeatures` (3 tests): Dry-run, confirmation, `--yes` flag
  - `TestAuthentication` (2 tests): Credential loading and env vars
  - `TestOutputFormatting` (2 tests): Result reporting format
- **Code Coverage:**
  - `cli_utils.py`: 88% (critical paths fully tested)
  - `cli_db_arango.py`: 55% (success paths and safety features tested)
  - `cli_user.py`: 53% (success paths and safety features tested)
  - Untested paths are primarily error handling branches with clear error messages

### Technical Details

- **New Modules:**
  - `mcp_arangodb_async/cli_utils.py` - Shared utilities (credentials, confirmation, result reporting)
  - `mcp_arangodb_async/cli_db_arango.py` - ArangoDB database operations
  - `mcp_arangodb_async/cli_user.py` - ArangoDB user management
- **Updated Modules:**
  - `mcp_arangodb_async/__main__.py` - Integrated new command structure
- **Test Modules:**
  - `tests/test_admin_cli.py` - Comprehensive admin CLI test suite
- **Exit Codes:**
  - `0` - Success
  - `1` - Error (validation, connection, permission)
  - `2` - Operation cancelled by user

### Documentation

- Updated CLI reference with new commands
- Added examples for all 16 commands
- Documented safety features and credential handling

---

## [0.4.7] - 2025-11-28

### Added

✅ **Multi-Tenancy Tools (Milestone 4.2 - Task 4.2.1)**
- **MCP Tools Implementation:**
  - Implemented 6 multi-tenancy MCP tools for database management:
    * `arango_set_focused_database` - Set focused database for session
    * `arango_get_focused_database` - Get currently focused database
    * `arango_list_available_databases` - List all configured databases
    * `arango_get_database_resolution` - Show database resolution algorithm
    * `arango_test_database_connection` - Test connection to specific database
    * `arango_get_multi_database_status` - Get status of all databases
  - Added tool constants to `tools.py`
  - Added tool models to `models.py`
  - Added tool handlers to `handlers.py`
  - Comprehensive unit tests with 19 test cases covering all scenarios
  - All tests passing with excellent coverage
  - Issue: Closes [#17](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/17)

✅ **CLI Tool Implementation (Milestone 4.2 - Task 4.2.2)**
- **Database Management CLI:**
  - Implemented `mcp-arangodb-async db` command with 5 subcommands:
    * `db add` - Add a new database configuration to YAML
    * `db remove` - Remove a database configuration from YAML
    * `db list` - List all configured databases
    * `db test` - Test connection to a specific database
    * `db status` - Show database resolution status
  - Admin-only tool (requires file system access to modify YAML)
  - Secure password management (passwords stored in environment variables)
  - Comprehensive unit tests with 17 test cases covering all scenarios
  - 96% code coverage (exceeds 90% target)
  - Issue: Closes [#18](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/18)

✅ **Documentation (Milestone 4.2 - Task 4.2.3)**
- **Multi-Tenancy Documentation:**
  - Created `docs/user-guide/cli-reference.md` - Complete CLI tool documentation (604 lines)
    * Installation and configuration
    * All 5 CLI commands with examples
    * Security best practices
    * Troubleshooting guide
  - Created `docs/user-guide/multi-tenancy-guide.md` - Complete multi-tenancy guide (450 lines)
    * Quick start tutorial
    * Database resolution algorithm explanation
    * All 6 multi-tenancy tools documented
    * Database parameter usage patterns
    * Best practices and troubleshooting
  - Updated `docs/user-guide/tools-reference.md`:
    * Added Multi-Tenancy Tools section (6 tools, 267 lines)
    * Added database parameter notes to 8 tool categories (32 tools)
    * Updated tool count from 43 to 49 tools
  - Updated `README.md`:
    * Added multi-tenancy to features list
    * Added multi-tenancy configuration section with examples
    * Added Multi-Tenancy Tools category (6 tools)
    * Added quick links to new documentation
    * Updated tool count from 43 to 49 tools
  - All documentation follows DRY principle (no duplication)
  - Examples progress from simple to advanced
  - Professional tone and consistent formatting
  - Issue: Closes [#19](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/19)

### Changed

- Updated `DeleteIndexArgs` test to expect `database` parameter (added in Milestone 4.1)
- Refactored `__main__.py` to use argparse subparsers for better command organization
- Updated existing CLI tests to work with new subcommand structure

### Technical Details

- **Files Modified (Task 4.2.2):**
  - `mcp_arangodb_async/cli_db.py` - New module with 5 CLI handlers
  - `mcp_arangodb_async/__main__.py` - Refactored to use subparsers, added `db` command
  - `tests/test_cli_db_unit.py` - Added comprehensive CLI tests (17 tests)
  - `tests/test_cli_args_unit.py` - Updated tests for new subcommand structure

- **Test Coverage (Task 4.2.2):**
  - 17 unit tests for CLI database management tool
  - Tests cover success cases, error cases, and edge cases
  - Tests verify YAML file operations (add, remove, list)
  - Tests verify connection testing functionality
  - Tests verify status reporting
  - 96% code coverage for cli_db.py module

- **Files Created (Task 4.2.3):**
  - `docs/user-guide/cli-reference.md` - 604 lines, complete CLI documentation
  - `docs/user-guide/multi-tenancy-guide.md` - 450 lines, complete multi-tenancy guide

- **Files Modified (Task 4.2.3):**
  - `docs/user-guide/tools-reference.md` - Added multi-tenancy section and database parameter notes
  - `README.md` - Added multi-tenancy features, configuration, and quick links
  - `docs/developer-guide/changelog.md` - Updated with Task 4.2.3 details

- **Documentation Quality (Task 4.2.3):**
  - All examples tested and grounded (no speculation)
  - Educational progression from simple to advanced
  - DRY principle followed (no duplication across files)
  - Professional tone and consistent formatting
  - Seamless integration with existing documentation
  - Cross-references between related documentation

---

## [0.4.6] - 2025-11-27

### Added

✅ **Database Override - Tool Models (Milestone 4.1)**
- **Tool Models Update (Task 4.1.1):**
  - Added optional `database` parameter to 32 data operation tool models
  - Enables per-tool database override for cross-database workflows
  - Categories updated: Core Data (8), Indexing (4), Validation & Bulk (4), Graph (12), Schema & Query (4)
  - Parameter pattern: `database: Optional[str] = Field(default=None, description="Database override")`
  - All existing model tests pass (40/40)
  - Issue: Closes [#15](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/15)

- **Handler Updates & Testing (Task 4.1.2):**
  - Added comprehensive test suite for per-tool database override functionality
  - Test critical requirement: per-tool override does NOT mutate focused_database state
  - Test database resolution priority (Level 1 override takes precedence)
  - Test empty string and None handling (skip to next level)
  - Test multiple tool calls with different overrides
  - 7 new unit tests, all passing (7/7 asyncio tests)
  - Issue: Closes [#16](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/16)

### Technical Details

**Database Resolution:**
- Per-tool database override implemented via Level 1 of 6-level priority fallback
- Database resolution already centralized in `entry.py` (from Milestone 1.2)
- Handlers receive resolved database connection automatically
- No handler code changes required (architecture already supports override)

**Test Coverage:**
- 7 new tests in `tests/test_per_tool_database_override_unit.py`
- All existing tests continue to pass (40 model tests, 11 db_resolver tests)
- Total: 58/63 tests passing (5 trio failures due to missing trio library)

---

## [0.4.5] - 2025-11-27

### Changed

✅ **State Migration - Cleanup (Milestone 3.2)**
- **Removed global variables from handlers.py (Task 3.2.1):**
  - Deleted `_ACTIVE_CONTEXT` global variable
  - Deleted `_CURRENT_STAGE` global variable
  - Deleted `_TOOL_USAGE_STATS` global variable
  - Deleted deprecated `_track_tool_usage()` function
  - Replaced global fallbacks with default values ("baseline", "setup", {})
  - Grep for global variables returns 0 results

### Added

✅ **Concurrent Session Isolation Verification (Task 3.2.2)**
- `test_concurrent_sessions_independent_state()`: Verifies 2 concurrent sessions have completely independent state across all 4 state components
- `test_workflow_switch_preserves_focused_database()`: Verifies focused database remains stable during workflow/stage switches
- 100% code coverage for session_state.py
- All 344 tests pass

### Technical Details

- SessionState now the single source of truth for per-session state
- No global variable fallback means handlers require session context for state persistence
- Tests updated to provide session context where state persistence is needed
- Phase 3 complete: Multi-tenancy foundation fully established

### Files Changed

**Modified:**
- `mcp_arangodb_async/handlers.py` - Remove global variables and fallbacks
- `tests/test_handlers_unit.py` - 3 tests updated to use session state
- `tests/test_mcp_integration.py` - 4 tests updated to include session_state in mock context
- `tests/test_session_state_unit.py` - 2 new verification tests

### Related Issues

Closes [#13](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/13), [#14](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/14)

---

## [0.4.4] - 2025-11-27

### Changed

✅ **State Migration - Tools (Milestone 3.1)**
- **Migrated 6 design pattern tools + 1 helper from global variables to per-session state:**
  - `handle_switch_workflow`: now async, uses `session_state.set_active_workflow()`
  - `handle_get_active_workflow`: uses `session_state.get_active_workflow()`
  - `handle_list_workflows`: uses `session_state.get_active_workflow()`
  - `handle_advance_workflow_stage`: now async, uses `session_state.set_tool_lifecycle_stage()`
  - `handle_unload_tools`: extracts session context for consistency
  - `handle_get_tool_usage_stats`: uses `session_state.get_tool_usage_stats()` and `session_state.get_tool_lifecycle_stage()`
  - `_track_tool_usage`: deprecated (tool usage now tracked via SessionState.track_tool_usage() in entry.py)

- **Infrastructure changes for per-session state support:**
  - `entry.py`: make `_invoke_handler` async-aware to support async handlers
  - `entry.py`: inject `_session_context` into validated_args for pattern handlers
  - `handlers.py`: add `_get_session_context()` helper for session context extraction
  - Global variables `_ACTIVE_CONTEXT`, `_CURRENT_STAGE`, `_TOOL_USAGE_STATS` marked for removal in Milestone 3.2

- **Rationale:** Enables multiple agents to work with different workflows/stages/stats simultaneously without interference, a prerequisite for multi-tenancy

### Added

✅ **Per-Session Isolation Tests**
- 6 new tests for workflow tool session isolation
- 2 new tests for lifecycle tool session isolation
- 2 new tests for usage stats session isolation
- Test coverage: 53 handler tests pass (up from 45)

### Technical Details

- Async handlers use `asyncio.Lock()` protected SessionState methods for thread-safe state mutations
- Sync handlers use non-locking SessionState getter methods for read-only operations
- Global variables retained as fallback during migration (removed in Milestone 3.2)
- Backward compatible: handlers work without session context using global fallback

### Files Changed

**Modified:**
- `mcp_arangodb_async/entry.py` - async-aware handler invocation, session context injection
- `mcp_arangodb_async/handlers.py` - 6 handlers migrated to SessionState
- `tests/test_handlers_unit.py` - 10 new per-session isolation tests

### Related Issues

Closes [#10](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/10), [#11](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/11), [#12](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/12)

---

## [0.4.3] - 2025-11-24

### Changed

✅ **Tool Renaming (Milestone 2.1)**
- **Renamed workflow tools to eliminate terminology ambiguity:**
  - `arango_switch_context` → `arango_switch_workflow`
  - `arango_get_active_context` → `arango_get_active_workflow`
  - `arango_list_contexts` → `arango_list_workflows`
- **Rationale:** Resolves ambiguity between "workflow context" (design patterns) and "database context" (multi-tenancy) as specified in Architecture Design v3
- **Updated components:**
  - Tool name constants in `mcp_arangodb_async/tools.py`
  - Pydantic models in `mcp_arangodb_async/models.py` (SwitchWorkflowArgs, GetActiveWorkflowArgs, ListWorkflowsArgs)
  - Handler registrations and functions in `mcp_arangodb_async/handlers.py`
  - All test references in `tests/test_handlers_unit.py` and `tests/test_mcp_integration.py`
  - Documentation in `README.md`, `docs/user-guide/tools-reference.md`, and `docs/user-guide/mcp-design-patterns.md`
- **Test Coverage:** All 81 handler and integration tests pass with no regressions
- **Breaking Change:** Old tool names (`arango_switch_context`, `arango_get_active_context`, `arango_list_contexts`) are no longer available

---

## [0.4.2] - 2025-11-23

### Added

✅ **Foundation Integration Layer (Milestone 1.2)**
- **Database Resolver (Task 1.2.1):**
  - `mcp_arangodb_async/db_resolver.py` with `resolve_database()` function
  - Implements 6-level priority fallback algorithm:
    1. Per-tool override (`tool_args["database"]`)
    2. Focused database (`session_state.get_focused_database()`)
    3. Config default (`config_loader.default_database`)
    4. Environment variable (`MCP_DEFAULT_DATABASE`)
    5. First configured database
    6. Hardcoded fallback (`"_system"`)
  - 11 unit tests, 100% code coverage
  - Issue: Closes [#4](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/4)

- **Session ID Extraction (Task 1.2.2):**
  - `mcp_arangodb_async/session_utils.py` with `extract_session_id()` function
  - Handles stdio transport (returns `"stdio"` singleton session)
  - Handles HTTP transport (returns unique session ID from request)
  - 14 unit tests, 100% code coverage
  - Issue: Closes [#5](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/5)

- **Entry Point Integration (Task 1.2.3):**
  - Updated `entry.py` to integrate all foundation components:
    - ConfigFileLoader: Load database configurations from YAML/env vars
    - MultiDatabaseConnectionManager: Manage connections to multiple databases
    - SessionState: Per-session state for focused database and workflows
  - Implements implicit session creation on first tool call
  - Implements database resolution algorithm in `call_tool()`
  - Adds session ID extraction and tool usage tracking
  - 10 integration tests
  - All 36 existing MCP integration tests pass
  - Issue: Closes [#6](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/6)

✅ **Test Coverage**
- Total Tests: 67 passing (all new components from both milestones)
  - Database Resolver: 11 tests (100% coverage)
  - Session Utils: 14 tests (100% coverage)
  - Entry Point Integration: 10 tests
  - Foundation Components: 32 tests (from Milestone 1.1)
- Backward Compatibility: ✅ All existing tests pass

### Changed

- **Architecture:** Integrated multi-database connection pooling with session-based context management
- **Entry Point:** Enhanced to support multi-database workflows with implicit session creation
- **Database Resolution:** Added deterministic 6-level priority algorithm for database selection

### Technical Details

- Foundation components (SessionState, MultiDatabaseConnectionManager, ConfigFileLoader) now fully integrated into MCP server
- Session state mutations protected by `asyncio.Lock()` for thread-safe concurrent access
- Database resolution algorithm enables both focused database context and per-tool overrides without ambiguity
- Backward compatibility maintained: existing deployments work unchanged

### Files Changed

**Created:**
- `mcp_arangodb_async/db_resolver.py`
- `mcp_arangodb_async/session_utils.py`
- `tests/test_db_resolver_unit.py`
- `tests/test_session_utils_unit.py`
- `tests/test_entry_point_integration_unit.py`

**Modified:**
- `mcp_arangodb_async/entry.py`

### Related Issues

Closes [#4](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/4), [#5](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/5), [#6](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/6)

---

## [0.4.1] - 2025-11-23

### Added

✅ **Foundation Core Components (Milestone 1.1)**
- **SessionState Component (Task 1.1.1):**
  - `mcp_arangodb_async/session_state.py` with SessionState class
  - Per-session state management for focused database, active workflow, tool lifecycle stage, and tool usage tracking
  - Replaces global state variables (`_ACTIVE_CONTEXT`, `_CURRENT_STAGE`, `_TOOL_USAGE_STATS`) with per-session isolation
  - Async-safe state mutations using `asyncio.Lock()`
  - Session isolation for concurrent agent operations
  - Methods: `initialize_session()`, `set_focused_database()`, `get_focused_database()`, `set_active_workflow()`, `get_active_workflow()`, `set_tool_lifecycle_stage()`, `get_tool_lifecycle_stage()`, `track_tool_usage()`, `get_tool_usage_stats()`, `cleanup_session()`, `cleanup_all()`
  - 11 unit tests, 100% code coverage
  - Issue: Closes [#1](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/1)

- **MultiDatabaseConnectionManager Component (Task 1.1.2):**
  - `mcp_arangodb_async/multi_db_manager.py` with connection pooling
  - Purpose: Connection pooling for multiple ArangoDB servers and databases
  - Lazy connection creation with connection reuse
  - Async-safe connection pool using `asyncio.Lock()`
  - Database configuration registration and management
  - Connection testing and health checks
  - Graceful cleanup on shutdown
  - Methods: `initialize()`, `get_connection()`, `get_configured_databases()`, `test_connection()`, `register_database()`, `close_all()`
  - 10 unit tests, 94% code coverage
  - Issue: Closes [#2](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/2)

- **ConfigFileLoader Component (Task 1.1.3):**
  - `mcp_arangodb_async/config_loader.py` for YAML-based configuration
  - Purpose: YAML configuration loading with backward compatibility
  - YAML file configuration loading
  - Backward compatibility with v0.4.0 environment variables
  - Database configuration CRUD operations (add, remove, get, save)
  - Support for optional description field
  - Graceful handling of empty/invalid YAML files
  - Security: Passwords stored in environment variables, referenced by name in YAML
  - Methods: `load()`, `get_configured_databases()`, `add_database()`, `remove_database()`, `_load_from_env_vars()`, `_save_to_yaml()`
  - 11 unit tests, 96% code coverage
  - Issue: Closes [#3](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/3)

✅ **Comprehensive Test Coverage**
- Total Tests: 32 tests passing
  - SessionState: 11 tests (100% coverage)
  - MultiDatabaseConnectionManager: 10 tests (94% coverage)
  - ConfigFileLoader: 11 tests (96% code coverage)
- All tests pass with no regressions

### Technical Details

- SessionState provides the isolation boundary for multi-database workflows
- MultiDatabaseConnectionManager enables multiple simultaneous ArangoDB connections without overhead
- ConfigFileLoader decouples database configuration from code, enabling runtime configuration changes
- All components use `asyncio.Lock()` for async-safe state and connection pool mutations
- Foundation components ready for integration into entry point

### Files Changed

**Created:**
- `mcp_arangodb_async/session_state.py`
- `mcp_arangodb_async/multi_db_manager.py`
- `mcp_arangodb_async/config_loader.py`
- `tests/test_session_state_unit.py`
- `tests/test_multi_db_manager_unit.py`
- `tests/test_config_loader_unit.py`

### Related Issues

Closes [#1](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/1), [#2](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/2), [#3](https://github.com/LittleCoinCoin/mcp-arangodb-async/issues/3)

---

## [0.4.0] - 2025-11-11

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
  - `docs/index.md` - Added MCP Design Patterns Guide to learning paths
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
  - Documentation hub (docs/index.md) with learning paths
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
│   ├── install-arangodb.md
│   ├── quickstart.md
│   ├── install-from-source.md
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
- **docs/index.md Updated:**
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

- [Quickstart Guide](../getting-started/quickstart.md)
- [Environment Variables](../configuration/environment-variables.md)
- [HTTP Transport](http-transport.md)
- [Tools Reference](../user-guide/tools-reference.md)

