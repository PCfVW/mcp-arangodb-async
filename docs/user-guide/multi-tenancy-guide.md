# Multi-Tenancy Overview (Top-level)

This page provides a concise, top-level explanation of how multi-tenancy works in MCP, the important concepts you need to know, and pointers to scenario-based step-by-step guides for hands-on setup.

**Audience:** End users and developers who want a quick, accurate orientation before diving into the scenario examples.

---

## Quick Overview

- Multi-tenancy allows one MCP server to manage multiple ArangoDB databases (same server or multiple instances).
- Use the CLI to register database configurations (stored in `config/databases.yaml`). Credentials are provided via environment variables referenced in the YAML (password env var names only; passwords are never stored in YAML files).
- You can either set a session-level focused database (most calls use it) or override the database per call using the `database` parameter.

---

## Quick Start (Top-level)

Follow these high-level steps. For full, step-by-step instructions and verification commands, see the scenario guides in the `multi-tenancy-scenarios/` directory.

1) Configure databases (CLI or edit YAML): register database entries and reference `password_env` variables.
  - Quick CLI example (see 01/02 scenario for a longer example):

```bash
maa db config add mydb --url http://localhost:8529 --database mydb --username admin --password-env ARANGO_PASSWORD
```

2) Ensure password environment variables are set (passwords bound to users, not to DB keys).

```bash
export ARANGO_PASSWORD='admin-password'
```

3) Start (or restart) the MCP server so it picks up config changes. Two common options:

- Use an MCP Host (recommended for interactive use) — Claude Desktop, LM Studio, etc. Configure the host to run the MCP server (stdio transport) so it can communicate with your assistant.
- Run the server directly in HTTP mode (for web clients or containerized deployments):

```bash
# Start server with default (stdio) transport
maa server

# Or start the HTTP transport so web clients can connect:
maa server --transport http --host 0.0.0.0 --port 8000
```

Note: Starting the server with default stdio (`maa server`) is useful primarily when run by an MCP Host (Claude Desktop, LM Studio, etc.) which manages the process lifecycle; running it interactively by itself is suitable only for manual testing and is not a supported UI for interactive use. If you want to connect from a web client or run in a container, start the HTTP transport as shown above. You can find more information in the [transport configuration guide](../configuration/transport-configuration.md).

4) Use the multi-tenancy tools (refer to the tools reference for parameters): list configured databases, set a focused database, check resolution, or override per-call.

<details>
<summary>💡 Advanced: Using shorthand aliases</summary>

**Quick configuration with short aliases:**
```bash
maa db config add mydb -u http://localhost:8529 -d mydb -U admin -P ARANGO_PASSWORD
```

**Quick updates with short aliases:**
```bash
# Update URL
maa db config update mydb -u http://new-host:8529

# Rename configuration
maa db config update mydb -k production

# Update multiple fields
maa db config update mydb -u http://new-host:8529 -d new_db --timeout 60
```

**Server startup with config alias:**
```bash
maa server -C config/databases.yaml
```

**Alias reference:**
- `-u` = `--url`
- `-d` = `--database`
- `-U` = `--username`
- `-k` = `--key` (for renaming)
- `-P` = `--arango-password-env` / `--pw-env`
- `-C` = `--config-file` / `--config-path`

See [CLI Reference](cli-reference.md) for complete list.
</details>

---

## Core Concepts

- Focused database: session-scoped database applied automatically to tools that don’t include a per-call override. Can be set with `arango_set_focused_database` or unset to revert to default resolution.
- Per-call database override: a `database` parameter passed to a tool call which supersedes the focused database for that call only.
- Passwords: the YAML file stores the env var name; actual secrets come from environment variables at runtime.

---

## Database Resolution (Concise)

When a tool call is executed, the database chosen is the result of a 6-level priority resolution (highest first):

1. Tool argument: `database` parameter passed in the tool call.
2. Focused database: set with `arango_set_focused_database` for the session.
3. Config default: `default_database` in YAML.
4. Environment variable: `ARANGO_DB` (treated as a database key when YAML config exists).
5. First configured: the first database listed in YAML.
6. Fallback: `_system` (hardcoded fallback).

> **Important:** In multi-tenancy mode, `ARANGO_DB` is treated as a **database key** (e.g., `first_db`, `production`), not a database name. It must match a key in your `config/databases.yaml`. See [Environment Variables](../configuration/environment-variables.md#arango_db) for details on the dual meaning of `ARANGO_DB`.

Note: Implementation is in `mcp_arangodb_async/db_resolver.py` if you want to inspect exact behavior.

---

## Recommended Tools (Top-level)

- `arango_list_available_databases` — list all configured database entries.
- `arango_set_focused_database` — set or unset the session-focused database.
- `arango_get_focused_database` — view the currently focused database.
- `arango_get_database_resolution` — show the resolution state and reason for a resolved database.
- `arango_database_status` / `arango_test_database_connection` — test connection and status for configured DBs.

For full parameter documentation, see `docs/user-guide/tools-reference.md`.

---

## Usage Patterns (Short)

- Focused database for routine workflows — set once, run many operations.
- Per-call database override for ad-hoc queries or cross-database comparison.
- Switch and verify: set focused database, call `arango_get_database_resolution` to confirm before critical updates.
- Unset focused database to revert to default resolution — useful after completing a workflow or switching contexts.

---

## Scenarios (Detailed, step-by-step)

Use the scenario pages for end-to-end examples that include commands, verification steps, and diagrams:

- [Scenario 1: Single Instance, Single Database](multi-tenancy-scenarios/01-single-instance-single-database.md) — starter tutorial for single DB setups.
- [Scenario 2: Single Instance, Multiple Databases](multi-tenancy-scenarios/02-single-instance-multiple-databases.md) — same ArangoDB instance with multiple databases.
- [Scenario 3: Multiple Instances, Multiple Databases](multi-tenancy-scenarios/03-multiple-instances-multiple-databases.md) — multiple ArangoDB hosts and instances.
- [Scenario 4: Agent-Based Access Control](multi-tenancy-scenarios/04-agent-based-access-control.md) — agent/role-based database access control examples.

---

## Quick Troubleshooting

- Wrong DB used: call `arango_get_database_resolution` and `arango_get_focused_database` to verify; ensure tools don’t accidentally include `database` overrides.
- DB not found: call `arango_list_available_databases` to verify the key exists, or add it with CLI.
- Connection failed: verify the env password, the URL/port, and use `arango_database_status` to check connectivity.

---

## Where to go next

1. Follow the scenario guide that best fits your setup (see Scenarios).
2. Use the tools reference (`docs/user-guide/tools-reference.md`) for invocation details and arguments.
3. Read `mcp_arangodb_async/db_resolver.py` to understand the exact behavior of the database resolution algorithm.

---

_This file is intentionally concise — for step-by-step procedure and verification commands, use the detailed scenario pages in the `multi-tenancy-scenarios/` directory._

---

## Quick Command Reference

These are the most common CLI commands and MCP tool invocations used across the scenario pages. They are intentionally short; find full parameter and example details in the scenarios or `docs/user-guide/cli-reference.md` and `docs/user-guide/tools-reference.md`.

- `maa db config add <key> --url <url> --database <db> --username <user> --password-env <ENV_VAR>` — Add or update a database entry in YAML config.
- `maa db add <db> --url <url> --username <user> --password-env <ENV_VAR>` — Create an ArangoDB database and user.
- `maa db config list` — List configured databases from the YAML config.
- `maa db config test <key>` — Test a configured database connection.
- `maa db list` — Show ArangoDB databases created in the server.
- `maa server` — Run the MCP server (stdio transport).
- `maa server transport http --host 0.0.0.0 --port 8000` — Run the MCP server in HTTP mode for web clients.

## Quick Prompt Examples

**"Focus on database db1"**
Expected tool call:

```json
{ "tool": "arango_set_focused_database", "arguments": { "database": "db1" } }
```

**"Find the first user in the database"**
Expected tool call: Run a query using the focused database:

```json
{ "tool": "arango_query", "arguments": { "query": "FOR doc IN users LIMIT 1 RETURN doc" } }
```

**"Which database will be used for the next operation?"**
Expected tool call: Check database status/resolution:

```json
{ "tool": "arango_database_status" }
```

---
