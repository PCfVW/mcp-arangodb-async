# CLI Reference

Complete documentation for the `mcp-arangodb-async` command-line interface.

**Audience:** System Administrators and DevOps Engineers  
**Prerequisites:** Python 3.11+, ArangoDB 3.11 installed & running
**Estimated Time:** 15-20 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Command Structure](#command-structure)
4. [Server Commands](#server-commands)
5. [Database Configuration Commands](#database-configuration-commands)
6. [Database Operations Commands](#database-operations-commands)
7. [User Management Commands](#user-management-commands)
8. [Health and Version Commands](#health-and-version-commands)
9. [Safety Features](#safety-features)
10. [Examples](#examples)
11. [Troubleshooting](#troubleshooting)
12. [Related Documentation](#related-documentation)

---

## Overview

The `mcp-arangodb-async` CLI provides comprehensive database and user management capabilities for ArangoDB. It supports two distinct workflows:

1. **YAML Configuration Management** - Manage databases exposed to the MCP server in `config/databases.yaml`
2. **Direct ArangoDB Operations** - Create/delete databases and manage users directly on ArangoDB server

---

## Installation

The CLI is included with the mcp-arangodb-async package:

```bash
pip install mcp-arangodb-async
```

Verify installation:

```bash
maa db --help
# Or: python -m mcp_arangodb_async db --help
```

**Note:** Both `maa` and `python -m mcp_arangodb_async` commands work. This guide uses `maa` for brevity.

---

## Command Structure

The CLI uses a hierarchical command structure:

```
maa
├── server              # Run MCP server (default)
├── health              # Health check
├── version             # Show version
├── db                  # Database management
│   ├── config          # YAML configuration management
│   │   ├── add         # Add database to YAML
│   │   ├── remove      # Remove database from YAML
│   │   ├── list        # List configured databases
│   │   ├── test        # Test database connection
│   │   ├── status      # Show resolution status
│   │   └── update      # Update database configuration
│   ├── add             # Create ArangoDB database
│   ├── remove          # Delete ArangoDB database
│   └── list            # List ArangoDB databases
└── user                # User management
    ├── add             # Create user
    ├── remove          # Delete user
    ├── list            # List users
    ├── grant           # Grant permissions
    ├── revoke          # Revoke permissions
    ├── databases       # List accessible databases (self-service)
    └── password        # Change password (self-service)
```

---

## Server Commands

### server

Run the MCP (Model Context Protocol) server.

**Syntax:**

```bash
maa server \
  [--transport <stdio|http>] \
  [--host <host>] \
  [--port <port>] \
  [--stateless] \
  [--config-file <path>]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `--config-file` | `--config-path`, `--cfgf`, `--cfgp`, `-C` | Path to database configuration YAML file (default: `ARANGO_DATABASES_CONFIG_FILE` env var, or `config/databases.yaml`) |
| `--transport` | - | Transport type: `stdio` or `http` (default: `stdio`, or from `MCP_TRANSPORT` env var) |
| `--host` | - | HTTP host address (default: `0.0.0.0`, or from `MCP_HTTP_HOST` env var). Only applies to HTTP transport |
| `--port` | - | HTTP port number (default: `8000`, or from `MCP_HTTP_PORT` env var). Only applies to HTTP transport |
| `--stateless` | - | Enable stateless mode for HTTP transport. In stateless mode, each request is independent |

**Transport Types:**

- **stdio** - Standard input/output transport. Suitable for integrating with Claude Desktop and other MCP clients that support stdio transport.
- **http** - HTTP transport. Runs the server as an HTTP service for remote access.

**Environment Variables:**

- `MCP_TRANSPORT` - Default transport type (overridden by `--transport`)
- `MCP_HTTP_HOST` - Default HTTP host (overridden by `--host`)
- `MCP_HTTP_PORT` - Default HTTP port (overridden by `--port`)
- `MCP_HTTP_STATELESS` - Enable stateless mode by default (set to `true` or `1`)
- `MCP_HTTP_CORS_ORIGINS` - CORS origins for HTTP transport (comma-separated, default: `*`)
- `ARANGO_DATABASES_CONFIG_FILE` - Path to database configuration file (overridden by `--config-file`)

**Example (Default - stdio):**

```bash
maa server
```

**Example (HTTP Transport):**

```bash
maa server --transport http --host 0.0.0.0 --port 8000
```

**Example (HTTP with Stateless Mode):**

```bash
maa server --transport http --stateless --port 9000
```

**Example (With Custom Config File):**

```bash
maa server --config-file /etc/arango/databases.yaml
```

**Example (Using Environment Variables):**

```bash
export MCP_TRANSPORT=http
export MCP_HTTP_HOST=localhost
export MCP_HTTP_PORT=8001
maa server
```

---

## Database Configuration Commands

These commands manage the YAML configuration file (`config/databases.yaml`). They do NOT connect to ArangoDB.

### db config add

Add a database configuration to YAML file.

**Syntax:**

```bash
maa db config add <key> \
  --url <url> \
  --database <database> \
  --username <username> \
  --arango-password-env <env_var> \
  [--timeout <seconds>] \
  [--description <text>] \
  [--config-file <path>] \
  [--dry-run] \
  [--yes]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `<key>` | - | Unique identifier for this configuration |
| `--url` | `-u` | ArangoDB server URL (e.g., `http://localhost:8529`) |
| `--database` | `-d` | Database name |
| `--username` | `-U` | Username for authentication |
| `--arango-password-env` | `--password-env`, `--pw-env`, `-P` | Environment variable name containing password |
| `--timeout` | - | Connection timeout in seconds (default: 30.0) |
| `--description` | - | Optional description |
| `--config-file` | `--config-path`, `--cfgf`, `--cfgp`, `-C` | Path to YAML file (default: `config/databases.yaml`) |
| `--dry-run` | - | Preview without executing |
| `--yes` | `-y` | Skip confirmation |

**Example:**

```bash
maa db config add production \
  --url http://localhost:8529 \
  --database myapp_prod \
  --username admin \
  --password-env ARANGO_PASSWORD \
  --timeout 60 \
  --description "Production database"
```

---

### db config remove

Remove a database configuration from YAML file.

**Syntax:**

```bash
maa db config remove <key> \
  [--config-file <path>] \
  [--dry-run] \
  [--yes]
```

**Aliases:** `rm`

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `<key>` | - | Configuration key to remove |
| `--config-file` | `--config-path`, `--cfgf`, `--cfgp`, `-C` | Path to YAML file (default: `config/databases.yaml`) |
| `--dry-run` | - | Preview without executing |
| `--yes` | `-y` | Skip confirmation |

**Example:**

```bash
maa db config remove staging
```

---

### db config list

List all configured databases from YAML file.

**Syntax:**

```bash
maa db config list [--config-file <path>]
```

**Aliases:** `ls`

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `--config-file` | `--config-path`, `--cfgf`, `--cfgp`, `-C` | Path to YAML file (default: `config/databases.yaml`) |

**Example:**

```bash
maa db config list
```

**Output:**

```
Configured databases (2):
Configuration file: config/databases.yaml
Default database: production

  production:
    URL: http://localhost:8529
    Database: myapp_prod
```

--- 

### db config update

Update an existing database configuration in YAML file.

**Syntax:**

```bash
maa db config update <existing-key> 
  [--key <new-key>] 
  [--url <url>] 
  [--database <database>] 
  [--username <username>] 
  [--arango-password-env <env_var>] 
  [--timeout <seconds>] 
  [--description <text>] 
  [--config-file <path>] 
  [--dry-run] 
  [--yes]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `<existing-key>` | - | Existing database key to update |
| `--key` | `-k` | New database key (rename the configuration) |
| `--url` | `-u` | ArangoDB server URL (e.g., `http://localhost:8529`) |
| `--database` | `-d` | Database name |
| `--username` | `-U` | Username for authentication |
| `--arango-password-env` | `--password-env`, `--pw-env`, `-P` | Environment variable name containing password |
| `--timeout` | - | Connection timeout in seconds |
| `--description` | - | Optional description (use empty string to clear) |
| `--config-file` | `--config-path`, `--cfgf`, `--cfgp`, `-C` | Path to YAML file (default: `config/databases.yaml`) |
| `--dry-run` | - | Preview without executing |
| `--yes` | `-y` | Skip confirmation |

**Output Format:**

Changes are displayed with before/after values:

```
[UPDATED] Database configuration 'production'
  Key: production → prod
  URL: http://localhost:8529 → http://new-host:8529
  Database: prod_db → new_db
  Username: admin → newuser
  Password Env: PROD_PASSWORD → NEW_PASSWORD
  Timeout: 30.0 → 60.0
  Description: Production database → Updated description
```

**Exit Codes:**

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (validation failed, file error, etc.) |
| 2 | Cancelled (user declined confirmation) |

**Examples:**

```bash
# Update URL only
maa db config update production --url http://new-host:8529

# Rename key only (long form)
maa db config update production --key prod

# Rename key only (short form)
maa db config update production -k prod

# Rename key and update fields
maa db config update production -k prod --url http://new-host:8529 --timeout 60

# Update multiple fields
maa db config update production \
  --url http://staging:8529 \
  --database staging_db \
  --timeout 45 \
  --description "Staging environment"

# Clear description (use empty string)
maa db config update production --description ""

# Dry-run mode (preview changes)
maa db config update production --url http://new:8529 --dry-run

# Skip confirmation
maa db config update production --url http://new:8529 --yes
```
    Username: admin
    Password env: ARANGO_PASSWORD
    Timeout: 60.0s
    Description: Production database

  staging:
    URL: http://localhost:8529
    Database: myapp_staging
    Username: admin
    Password env: ARANGO_PASSWORD
    Timeout: 30.0s
    Description: Staging database
```

---

### db config test

Test connection to a configured database.

**Syntax:**

```bash
maa db config test <key> [--config-file <path>]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `<key>` | - | Configuration key to test |
| `--config-file` | `--config-path`, `--cfgf`, `--cfgp`, `-C` | Path to YAML file (default: `config/databases.yaml`) |

**Example:**

```bash
maa db config test production
```

**Output (Success):**

```
✓ Connection to 'production' successful
  ArangoDB version: 3.11.0
```

**Output (Failure):**

```
✗ Connection to 'production' failed
  Error: Connection refused
```

**Exit Codes:**
- `0` - Success
- `1` - Failure

---

### db config status

Show database resolution status and configuration overview.

**Syntax:**

```bash
maa db config status [--config-file <path>]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `--config-file` | `--config-path`, `--cfgf`, `--cfgp`, `-C` | Path to YAML file (default: `config/databases.yaml`) |

**Example:**

```bash
maa db config status
```

**Output:**

```
Database Resolution Status:
Configuration file: config/databases.yaml

Default database (from config): production
Default database (from ARANGO_DB): Not set

Configured databases: 2
  - production
  - staging

Resolution order:
  1. Tool argument (database parameter)
  2. Focused database (session state)
  3. Config default (from YAML)
  4. Environment variable (ARANGO_DB)
  5. First configured database
  6. Fallback to '_system'
```

---

## Database Operations Commands

These commands manage ArangoDB databases directly on the server. They require root credentials.

### db add

Create a new ArangoDB database.

**Syntax:**

```bash
maa db add <name> \
  [--with-user <username>] \
  [--permission <rw|ro|none>] \
  [--url <url>] \
  [--environment-file <path>] \
  [--arango-root-password-env <var>] \
  [--arango-password-env <var>] \
  [--dry-run] \
  [--yes]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `<name>` | - | Database name to create |
| `--with-user` | - | Username to grant access (creates user if not exists) |
| `--permission` | `--perm`, `-p` | Permission level: `rw`, `ro`, `none` (default: `rw`) |
| `--url` | `-u` | ArangoDB URL (default: `ARANGO_URL` env or `http://localhost:8529`) |
| `--environment-file` | `--env-file`, `--envf`, `-E` | Path to .env file for credentials |
| `--arango-root-password-env` | `--root-pw-env`, `-R` | Root password env var (default: `ARANGO_ROOT_PASSWORD`) |
| `--arango-password-env` | `--password-env`, `--pw-env`, `-P` | User password env var (default: `ARANGO_PASSWORD`) |
| `--dry-run` | - | Preview without executing |
| `--yes` | `-y` | Skip confirmation |

**Example (Simple):**

```bash
export ARANGO_ROOT_PASSWORD="root-password"
maa db add myapp_prod
```

**Example (Atomic with User):**

```bash
export ARANGO_ROOT_PASSWORD="root-password"
export ARANGO_PASSWORD="user-password"

maa db add myapp_prod \
  --with-user myapp_user \
  --permission rw
```

**Output:**

```
✓ Database 'myapp_prod' created
✓ User 'myapp_user' created (active: true)
✓ Permission rw granted: myapp_user → myapp_prod
```

---

### db remove

Delete an ArangoDB database.

**Syntax:**

```bash
maa db remove <name> \
  [--url <url>] \
  [--environment-file <path>] \
  [--arango-root-password-env <var>] \
  [--dry-run] \
  [--yes]
```

**Aliases:** `rm`

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `<name>` | - | Database name to delete |
| `--url` | `-u` | ArangoDB URL (default: `ARANGO_URL` env or `http://localhost:8529`) |
| `--environment-file` | `--env-file`, `--envf`, `-E` | Path to .env file for credentials |
| `--arango-root-password-env` | `--root-pw-env`, `-R` | Root password env var (default: `ARANGO_ROOT_PASSWORD`) |
| `--dry-run` | - | Preview without executing |
| `--yes` | `-y` | Skip confirmation |

**Safety:** Cannot delete `_system` database.

**Example:**

```bash
export ARANGO_ROOT_PASSWORD="root-password"
maa db remove myapp_staging
```

**Output:**

```
⚠️  This will:
  - Remove database 'myapp_staging'
  - Revoke permission: myapp_user → myapp_staging (was: rw)

Are you sure you want to proceed? [y/N]: y

✓ Database 'myapp_staging' removed
```

---

### db list

List all ArangoDB databases.

**Syntax:**

```bash
maa db list \
  [--url <url>] \
  [--environment-file <path>] \
  [--arango-root-password-env <var>] \
  [--json]
```

**Aliases:** `ls`

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `--url` | `-u` | ArangoDB URL (default: `ARANGO_URL` env or `http://localhost:8529`) |
| `--environment-file` | `--env-file`, `--envf`, `-E` | Path to .env file for credentials |
| `--arango-root-password-env` | `--root-pw-env`, `-R` | Root password env var (default: `ARANGO_ROOT_PASSWORD`) |
| `--json` | - | Output in JSON format |

**Example:**

```bash
export ARANGO_ROOT_PASSWORD="root-password"
maa db list
```

**Output:**

```
Databases (3):
  - _system (system)
  - myapp_prod
  - myapp_staging
```

**Example (JSON):**

```bash
maa db list --json
```

**Output:**

```json
["_system", "myapp_prod", "myapp_staging"]
```

---

## User Management Commands

These commands manage ArangoDB users and permissions.

### user add

Create a new ArangoDB user (admin operation).

**Syntax:**

```bash
maa user add <username> \
  [--active] \
  [--url <url>] \
  [--environment-file <path>] \
  [--arango-root-password-env <var>] \
  [--arango-password-env <var>] \
  [--dry-run] \
  [--yes]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `<username>` | - | Username to create |
| `--active` | - | User is active (default: true) |
| `--url` | `-u` | ArangoDB URL (default: `ARANGO_URL` env or `http://localhost:8529`) |
| `--environment-file` | `--env-file`, `--envf`, `-E` | Path to .env file for credentials |
| `--arango-root-password-env` | `--root-pw-env`, `-R` | Root password env var (default: `ARANGO_ROOT_PASSWORD`) |
| `--arango-password-env` | `--password-env`, `--pw-env`, `-P` | User password env var (default: `ARANGO_PASSWORD`) |
| `--dry-run` | - | Preview without executing |
| `--yes` | `-y` | Skip confirmation |

**Example:**

```bash
export ARANGO_ROOT_PASSWORD="root-password"
export ARANGO_PASSWORD="user-password"

maa user add myapp_user
```

---

### user remove

Delete an ArangoDB user (admin operation).

**Syntax:**

```bash
maa user remove <username> \
  [--url <url>] \
  [--environment-file <path>] \
  [--arango-root-password-env <var>] \
  [--dry-run] \
  [--yes]
```

**Aliases:** `rm`

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `<username>` | - | Username to delete |
| `--url` | `-u` | ArangoDB URL (default: `ARANGO_URL` env or `http://localhost:8529`) |
| `--environment-file` | `--env-file`, `--envf`, `-E` | Path to .env file for credentials |
| `--arango-root-password-env` | `--root-pw-env`, `-R` | Root password env var (default: `ARANGO_ROOT_PASSWORD`) |
| `--dry-run` | - | Preview without executing |
| `--yes` | `-y` | Skip confirmation |

**Safety:** Cannot delete `root` user.

**Example:**

```bash
export ARANGO_ROOT_PASSWORD="root-password"
maa user remove old_user
```

---

### user list

List all ArangoDB users (admin operation).

**Syntax:**

```bash
maa user list \
  [--url <url>] \
  [--environment-file <path>] \
  [--arango-root-password-env <var>] \
  [--json]
```

**Aliases:** `ls`

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `--url` | `-u` | ArangoDB URL (default: `ARANGO_URL` env or `http://localhost:8529`) |
| `--environment-file` | `--env-file`, `--envf`, `-E` | Path to .env file for credentials |
| `--arango-root-password-env` | `--root-pw-env`, `-R` | Root password env var (default: `ARANGO_ROOT_PASSWORD`) |
| `--json` | - | Output in JSON format |

**Example:**

```bash
export ARANGO_ROOT_PASSWORD="root-password"
maa user list
```

**Output:**

```
Users (3):
  - root (active)
  - myapp_user (active)
  - readonly_user (inactive)
```

---

### user grant

Grant database permissions to a user (admin operation).

**Syntax:**

```bash
maa user grant <username> <database> \
  [--permission <rw|ro|none>] \
  [--url <url>] \
  [--environment-file <path>] \
  [--arango-root-password-env <var>] \
  [--dry-run] \
  [--yes]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `<username>` | - | Username to grant permissions to |
| `<database>` | - | Database name |
| `--permission` | `--perm`, `-p` | Permission level: `rw`, `ro`, `none` (default: `rw`) |
| `--url` | `-u` | ArangoDB URL (default: `ARANGO_URL` env or `http://localhost:8529`) |
| `--environment-file` | `--env-file`, `--envf`, `-E` | Path to .env file for credentials |
| `--arango-root-password-env` | `--root-pw-env`, `-R` | Root password env var (default: `ARANGO_ROOT_PASSWORD`) |
| `--dry-run` | - | Preview without executing |
| `--yes` | `-y` | Skip confirmation |

**Permission Levels:**
- `rw` - Read-write access (full CRUD operations)
- `ro` - Read-only access (queries only)
- `none` - No access (revokes permissions)

**Example:**

```bash
export ARANGO_ROOT_PASSWORD="root-password"
maa user grant myapp_user myapp_prod --permission rw
```

---

### user revoke

Revoke database permissions from a user (admin operation).

**Syntax:**

```bash
maa user revoke <username> <database> \
  [--url <url>] \
  [--environment-file <path>] \
  [--arango-root-password-env <var>] \
  [--dry-run] \
  [--yes]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `<username>` | - | Username to revoke permissions from |
| `<database>` | - | Database name |
| `--url` | `-u` | ArangoDB URL (default: `ARANGO_URL` env or `http://localhost:8529`) |
| `--environment-file` | `--env-file`, `--envf`, `-E` | Path to .env file for credentials |
| `--arango-root-password-env` | `--root-pw-env`, `-R` | Root password env var (default: `ARANGO_ROOT_PASSWORD`) |
| `--dry-run` | - | Preview without executing |
| `--yes` | `-y` | Skip confirmation |

**Example:**

```bash
export ARANGO_ROOT_PASSWORD="root-password"
maa user revoke myapp_user old_database
```

---

### user databases

List databases accessible to current user (self-service operation).

**Syntax:**

```bash
maa user databases \
  [--url <url>] \
  [--environment-file <path>] \
  [--arango-password-env <var>] \
  [--json]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `--url` | `-u` | ArangoDB URL (default: `ARANGO_URL` env or `http://localhost:8529`) |
| `--environment-file` | `--env-file`, `--envf`, `-E` | Path to .env file for credentials |
| `--arango-password-env` | `--password-env`, `--pw-env`, `-P` | User password env var (default: `ARANGO_PASSWORD`) |
| `--json` | - | Output in JSON format |

**Note:** Uses current user's credentials (not root).

**Example:**

```bash
export ARANGO_USERNAME="myapp_user"
export ARANGO_PASSWORD="user-password"

maa user databases
```

**Output:**

```
Accessible databases for user 'myapp_user' (2):
  - myapp_prod
  - myapp_staging
```

---

### user password

Change current user's password (self-service operation).

**Syntax:**

```bash
maa user password \
  [--url <url>] \
  [--environment-file <path>] \
  [--arango-password-env <var>] \
  [--arango-new-password-env <var>] \
  [--dry-run] \
  [--yes]
```

**Arguments:**

| Argument | Aliases | Description |
|----------|---------|-------------|
| `--url` | `-u` | ArangoDB URL (default: `ARANGO_URL` env or `http://localhost:8529`) |
| `--environment-file` | `--env-file`, `--envf`, `-E` | Path to .env file for credentials |
| `--arango-password-env` | `--password-env`, `--pw-env`, `-P` | Current password env var (default: `ARANGO_PASSWORD`) |
| `--arango-new-password-env` | `--new-password-env`, `--new-pw-env`, `-N` | New password env var (default: `ARANGO_NEW_PASSWORD`) |
| `--dry-run` | - | Preview without executing |
| `--yes` | `-y` | Skip confirmation |

**Example:**

```bash
export ARANGO_USERNAME="myapp_user"
export ARANGO_PASSWORD="old-password"
export ARANGO_NEW_PASSWORD="new-secure-password"

maa user password
```

---

## Health and Version Commands

### health

Run health check and output JSON.

**Syntax:**

```bash
maa health
```

**Output:**

```json
{
  "ok": true,
  "status": "healthy",
  "url": "http://localhost:8529",
  "database": "_system",
  "username": "root",
  "info": {
    "version": "3.11.0"
  }
}
```

**Exit Codes:**
- `0` - Healthy
- `1` - Unhealthy

---

### version

Display version information.

**Syntax:**

```bash
maa version
```

**Output:**

```
mcp-arangodb-async version 0.3.2
Python 3.11.0
```

---

## Safety Features

### Interactive Confirmations

All destructive operations require confirmation:

```bash
maa db remove myapp_staging
```

**Output:**

```
⚠️  This will:
  - Remove database 'myapp_staging'
  - Revoke permission: myapp_user → myapp_staging (was: rw)

Are you sure you want to proceed? [y/N]:
```

### Dry-Run Mode

Preview changes without executing:

```bash
maa db add myapp_test \
  --with-user test_user \
  --dry-run
```

**Output:**

```
⚠️  DRY RUN - No changes will be made

This would:
  + Add database 'myapp_test'
  + Add user 'test_user' (active: true)
  + Grant permission rw: test_user → myapp_test
```

### Automation Mode

Skip confirmations with `--yes` flag:

```bash
maa db remove myapp_staging --yes
```

Or set environment variable:

```bash
export MCP_ARANGODB_ASYNC_CLI_YES=1
maa db remove myapp_staging
```

### Exit Codes

| Code | Meaning | When |
|------|---------|------|
| `0` | Success | Operation completed successfully |
| `1` | Error | Invalid input, connection failure, operation failed |
| `2` | Cancelled | User declined confirmation |

---

## Examples

### Example 1: Complete Setup

```bash
# Set credentials
export ARANGO_ROOT_PASSWORD="root-password"
export ARANGO_PASSWORD="user-password"

# Create database with user (atomic)
maa db add myapp_prod \
  --with-user myapp_user \
  --permission rw

# Add to YAML config
maa db config add production \
  --url http://localhost:8529 \
  --database myapp_prod \
  --username myapp_user \
  --password-env ARANGO_PASSWORD \
  --description "Production database"

# Test connection
maa db config test production

# Verify
maa db list
maa db config list
```

---

### Example 2: Permission Management

```bash
export ARANGO_ROOT_PASSWORD="root-password"

# Grant read-write to production
maa user grant myapp_user myapp_prod --permission rw

# Grant read-only to staging
maa user grant myapp_user myapp_staging --permission ro

# Verify user's access
export ARANGO_USERNAME="myapp_user"
export ARANGO_PASSWORD="user-password"
maa user databases
```

---

### Example 3: Using .env Files

Create `.env.production`:

```dotenv
ARANGO_URL=http://prod-server:8529
ARANGO_ROOT_PASSWORD=prod-root-password
ARANGO_PASSWORD=prod-user-password
```

Use with commands:

```bash
maa db add myapp_prod \
  --env-file .env.production \
  --with-user myapp_user
```

---

## Troubleshooting

### Connection Refused

**Problem:** Cannot connect to ArangoDB

**Solution:**

1. Verify ArangoDB is running:
```bash
curl http://localhost:8529/_api/version
```

2. Check URL in configuration:
```bash
maa db config list
```

3. Verify credentials:
```bash
echo $ARANGO_ROOT_PASSWORD
```

---

### Permission Denied

**Problem:** Cannot write to config file

**Solution:**

```bash
# Linux/macOS
chmod 600 config/databases.yaml

# Windows
icacls config\databases.yaml /inheritance:r /grant:r "%USERNAME%:F"
```

---

### User Already Exists

**Problem:** User creation fails because user exists

**Solution:**

Use `--with-user` with `db add` - it handles existing users automatically:

```bash
maa db add myapp_prod \
  --with-user existing_user \
  --permission rw
```

---

## Related Documentation

- [Multi-Tenancy Guide](multi-tenancy-guide.md) - Using multiple databases
- [Tools Reference](tools-reference.md) - MCP tools
- [Quickstart Guide](../getting-started/quickstart.md) - Setup instructions
- [Troubleshooting](troubleshooting.md) - Common issues

---

**Next Steps:**

1. Set up your databases using `db add` or `db config add`
2. Test connections using `db config test`
3. Start the MCP server: `maa server`
4. Read the [Multi-Tenancy Guide](multi-tenancy-guide.md) for usage patterns
