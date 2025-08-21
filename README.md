# ArangoDB MCP Server for Python

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/Protocol-MCP-%23555555)](https://modelcontextprotocol.io/)

A minimal, production-friendly MCP stdio server exposing ArangoDB operations to MCP clients (e.g., Claude Desktop, Augment Code). Async-first Python, wrapping the official `python-arango` driver. Safe, high-value tools for queries, collections/indexes, graphs, and JSON Schema validation. This guide assumes ArangoDB runs via Docker Compose using the provided `docker-compose.yml`.

Note: Licensing changes for ArangoDB 3.12+ are summarized in the appendix; see “Appendix: License Notes (ArangoDB)”.

---

## Architecture at a Glance

Your AI Assistant interacts with this server, which in turn commands your local ArangoDB instance.

```
+------------------------+      +-------------------------+      +----------------------+
|   MCP Client           |      |   ArangoDB MCP Server   |      |   ArangoDB           |
| (Claude, Augment, etc.)|----->|   (This Python Repo)    |----->|   (Docker Container) |
+------------------------+      +-------------------------+      +----------------------+
```

## Table of Contents
- [Architecture at a Glance](#architecture-at-a-glance)
- [Why Run ArangoDB in Docker?](#why-run-arangodb-in-docker)
- [First tests (PowerShell)](#first-tests-powershell)
- [Using Aardvark (Web UI)](#using-aardvark-web-ui)
- [Troubleshooting (PowerShell)](#troubleshooting-powershell)
- [Exposed MCP Tools](#exposed-mcp-tools)
- [Not Implemented (by Design)](#not-implemented-by-design)
- [Quick Start (Windows)](#quick-start-windows)
- [First Successful Interaction](#first-successful-interaction)
- [Example Use Cases](#example-use-cases)
- [Appendix A: License Notes (ArangoDB)](#appendix-a-license-notes-arangodb)
- [Appendix B: Python File Index](#appendix-b-python-file-index)
- [References](#references)

---


## Why Run ArangoDB in Docker?
- Stability and isolation: avoid host conflicts and “works on my machine” issues.
- Zero-install DB: start/stop with `docker compose`.
- Reproducibility: same image/tag across teammates and CI.
- Health checks baked-in: readiness validation in compose.
- Fast reset: recreate clean instances easily.
- Portability: consistent on Windows/macOS/Linux.

Persistent data (recommended)

Edit your `docker-compose.yml`. Replace the `arangodb` service with the snippet below and add the `volumes:` block at the end. This pins the image to 3.11 (the version used to develop/test here) and preserves data across container restarts.

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

## First tests (PowerShell)

Use [Windows PowerShell](https://learn.microsoft.com/powershell/) for the following commands. Run them from the repo root next to `docker-compose.yml`.

1) Start the DB

```powershell
docker compose up -d arangodb
docker compose ps arangodb
```

Expected STATUS: Up (healthy)

2) Verify server health via module CLI

Create a `.env` (copy from `env.example`) and ensure it contains:

```
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
```

Then run:

```powershell
python -m mcp_arangodb --health
```

Expected JSON: `{"ok": true, ... "db": "mcp_arangodb_test", "user": "mcp_arangodb_user"}`

3) Initialize app database and user (one-time)

```powershell
pwsh -File .\scripts\setup-arango.ps1
```

If you changed the root password in `.env` (`ARANGO_ROOT_PASSWORD`), pass it:

```powershell
pwsh -File .\scripts\setup-arango.ps1 -RootPassword "your_root_pw"
```

4) Try the MCP stdio client demo

```powershell
python .\scripts\mcp_stdio_client.py --demo --collection users
```

You should see:

- Tools list printed
- Create collection result
- Insert result
- Query rows with the inserted document

If you omit `--demo`, it will just list collections.

## Using Aardvark (Web UI)

The ArangoDB admin UI (Aardvark) runs inside the container and is exposed on your host.

1) Open the UI

```text
http://localhost:8529
```

2) Log in

- Username: `mcp_arangodb_user` (or `root` for admin tasks)
- Password: value from your `.env` (`ARANGO_PASSWORD` for app user, `ARANGO_ROOT_PASSWORD` for root)

3) Select the database

- In the top bar, change the database to `mcp_arangodb_test`.
- Go to “Collections” to see user collections (system collections start with `_`).

4) Optional: run a quick AQL query

Open “Queries” and execute:

```aql
FOR d IN @@col LIMIT 5 RETURN d
```

Bind parameters:

```json
{
  "@col": "users"
}
```

If you haven’t created `users`, use the demo client above or create a collection from the UI first.

## Troubleshooting (PowerShell)

These are the most common issues and fixes observed during setup.

- **Wrong env vars or old values in session**

  Symptoms: `python -m mcp_arangodb --health` shows db/user as `mcp_test`/`mcp_user` or unexpected values.

  Fix:
  ```powershell
  # Clear stale values to prefer .env
  Remove-Item Env:ARANGO_URL,Env:ARANGO_DB,Env:ARANGO_USERNAME,Env:ARANGO_PASSWORD -ErrorAction SilentlyContinue
  Remove-Item Env:ARANGO_USER,Env:ARANGO_PASS -ErrorAction SilentlyContinue
  # Re-run from repo root so python-dotenv finds .env
  python -m mcp_arangodb --health
  ```

- **HTTP 401 Unauthorized**

  Symptom: `{"ok": false, "error": "[HTTP 401] not authorized"}`

  Cause: App user/database not created or wrong password.

  Fix:
  ```powershell
  pwsh -File .\scripts\setup-arango.ps1
  # If ARANGO_ROOT_PASSWORD differs from default 'changeme':
  # pwsh -File .\scripts\setup-arango.ps1 -RootPassword "your_root_pw"
  ```

- **Container unhealthy (healthcheck uses curl)**

  Symptom: `docker inspect ... Health.Log` shows `curl: not found`.

  Fix: Healthcheck uses `arangosh` in this repo. Ensure your `docker-compose.yml` matches the snippet above. Then recreate:
  ```powershell
  docker compose down
  docker compose up -d arangodb
  docker compose ps arangodb
  ```

- **MCP stdio client shows "Database unavailable"**

  Symptom from `scripts/mcp_stdio_client.py` when listing collections.

  Causes and fixes:
  - Server started before DB was ready. Re-run; a lazy connect fallback now attempts to connect on first tool call.
  - Env not reaching the child process. The client now launches with the same Python (`sys.executable`) and passes your full environment; ensure `.env` exists at repo root.
  - For verbose logs:
    ```powershell
    $env:LOG_LEVEL="DEBUG"
    python -m mcp_arangodb.entry
    ```

- **Manual sanity checks**

  ```powershell
  # HTTP ping
  curl http://localhost:8529/_api/version

  # arangosh as app user
  docker compose exec arangodb arangosh --server.username mcp_arangodb_user --server.password mcp_arangodb_password --server.database mcp_arangodb_test --javascript.execute-string "require('@arangodb').db._collections().map(c=>c.name())"

Tip: If you already ran a non-persistent setup, run `docker compose down` then `docker compose up -d` after adding the volume. For a bind mount on Windows: `"D:/arangodb-data:/var/lib/arangodb3"`.

---

## Exposed MCP Tools

Each tool has strict Pydantic schemas and is handled in `mcp_arangodb/entry.py` and `mcp_arangodb/handlers.py`.

#### At a glance
- Core essentials: CRUD, discovery, collection setup, backup
- Indexing & analysis: list/create/delete indexes, explain queries
- Validation & bulk ops: reference validation, validated insert, bulk insert/update
- Schema tools: create schema, validate document
- Enhanced query: query builder, query profile
- Graph tools: create graph, add edge, traverse, shortest path, list graphs, add vertex/edge defs
- Aliases: traversal alias, add-vertex alias

#### Full list
- Core essentials
  - arango_query — Execute AQL with optional bind vars; returns rows.
  - arango_list_collections — List non-system collections.
  - arango_insert — Insert a document into a collection.
  - arango_update — Update a document by key in a collection.
  - arango_remove — Remove a document by key from a collection.
  - arango_create_collection — Create a collection (document or edge) or return properties.
  - arango_backup — Backup collections to JSON files (filesystem side-effect only).
- Indexing & analysis
  - arango_list_indexes — List indexes for a collection (simplified fields).
  - arango_create_index — Create index (persistent, hash, skiplist, ttl, fulltext, geo).
  - arango_delete_index — Delete index by id or name.
  - arango_explain_query — Explain AQL and return plans/warnings/stats.
- Validation & bulk ops
  - arango_validate_references — Validate that reference fields point to existing docs.
  - arango_insert_with_validation — Insert after reference validation.
  - arango_bulk_insert — Batch insert with error accounting.
  - arango_bulk_update — Batch update by key.
- Schema tools
  - arango_create_schema — Create or update a named JSON Schema.
  - arango_validate_document — Validate a document against stored or inline schema.
- Enhanced query helpers
  - arango_query_builder — Build simple AQL with filters/sort/limit; project or full docs.
  - arango_query_profile — Explain a query and return plans/stats for profiling.
- Graph tools
  - arango_create_graph — Create a named graph with edge definitions.
  - arango_add_edge — Insert an edge between vertices with optional attributes.
  - arango_traverse — Traverse a graph from a start vertex with depth bounds.
  - arango_shortest_path — Compute shortest path between two vertices.
  - arango_list_graphs — List graphs in the database.
  - arango_add_vertex_collection — Add a vertex collection to a graph.
  - arango_add_edge_definition — Create an edge definition for a graph.
- Aliases
  - arango_graph_traversal — Alias for arango_traverse.
  - arango_add_vertex — Alias for arango_insert (clarity in graph workflows).

#### Toolset gating:
- You may restrict the toolset (e.g., for compatibility tests) using `MCP_COMPAT_TOOLSET` (e.g., `baseline`, `full`). Omit for full toolset by default.

---

## Not Implemented (by Design)
- Database creation/deletion — Elevated privileges on `_system`; handled by ops/IaC or setup scripts.
- Listing all databases — Admin-only and can disclose tenant names; if ever added, gate and limit to accessible DBs.

These choices reduce misuse, respect least privilege, and keep this server focused on application-level tasks.

---

## Quick Start (Windows)

Prerequisites
- Docker Desktop (for ArangoDB)
- Python 3.11+

1) Clone and install dependencies
```powershell
git clone https://github.com/ravenwits/mcp-server-arangodb-python.git
cd "mcp-server-arangodb-python"
python -m pip install -r requirements.txt
```

2) Start ArangoDB (via Docker)
```powershell
# In repo root
docker compose up -d
```

3) Initialize database and user (convenience script)
```powershell
# Creates database mcp_arangodb_test and user mcp_arangodb_user/mcp_arangodb_password by default
scripts\setup-arango.ps1 -RootPassword "changeme" -DbName "mcp_arangodb_test" -User "mcp_arangodb_user" -Password "mcp_arangodb_password" -Seed
```

4) Configure environment (.env recommended)
```powershell
# Create a local .env from the template (kept untracked by .gitignore)
Copy-Item env.example .env
# Edit .env and set real values as needed (no quotes required in .env)
notepad .env
```

Example .env contents (matches this repo's defaults):
```dotenv
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password

# Optional tuning
ARANGO_TIMEOUT_SEC=30.0
# Compatibility: limit toolset (used in tests); omit for full
# MCP_COMPAT_TOOLSET=baseline
```

Notes:
- Docker Compose automatically reads variables from `.env` in the repo root (used for `ARANGO_ROOT_PASSWORD`).
- The application also loads `.env` at runtime via `python-dotenv` in `mcp_arangodb/config.py`.
- If you prefer, you can still export variables for the current shell session instead of using `.env`:
```powershell
$env:ARANGO_URL = "http://localhost:8529"
$env:ARANGO_DB = "mcp_arangodb_test"
$env:ARANGO_USERNAME = "mcp_arangodb_user"
$env:ARANGO_PASSWORD = "mcp_arangodb_password"
$env:ARANGO_TIMEOUT_SEC = "30.0"
```

5) Run the MCP server (stdio)
```powershell
python -m mcp_arangodb
```
The server communicates over stdio per MCP; clients (e.g., Claude Desktop, Augment Code) will spawn it and talk over stdin/stdout.

---

## First Successful Interaction

Claude Desktop (MCP)
- Add a server entry in your Claude MCP config to launch this repo’s stdio server:
```json
{
  "mcpServers": {
    "arangodb": {
      "command": "python",
      "args": ["-m", "mcp_arangodb"],
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
- Where to add this in Claude Desktop: add your MCP server via Claude Desktop settings per the official guides. See:
  - Model Context Protocol quickstart (user): https://modelcontextprotocol.io/quickstart/user
  - Anthropic Support – Getting started with local MCP servers (Claude Desktop): https://support.anthropic.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop
- First prompt to try: "List all collections in my database."

### Next Steps: Your First Write

After listing collections, try a simple write-and-read cycle to confirm full functionality.

1.  **Create a document**:
    *   Prompt: `Use the arango_insert tool to add {'name': 'test_document', 'value': 1} to a new collection named 'tests'.`
2.  **Verify the document**:
    *   Prompt: `Use arango_query to find and return the document you just created in the 'tests' collection.`

This confirms your environment is fully configured for both reading from and writing to the database.

---

## Example Use Cases

- Claude Desktop (MCP)
  - Unexpected prompt ideas:
    - Music: "Build a piano‑jazz knowledge graph of Artists, Albums, Sub‑genres, and Influence edges from this small JSON. Create indexes, then traverse to curate a 10‑track piano‑jazz lineage playlist starting from 'Michel Petrucciani'. Export to JSON."
    - Space: "Model missions, spacecraft, instruments, targets (Mars, Europa…) as vertices and 'observed_with' edges. Find shortest paths from 'ion propulsion' to 'first detection of water ice' via technology lineage. Profile the query and suggest indexes."
    - Travel: "Create a city graph with edges = flights (cost, CO2, duration). Given 5 candidate cities, compute a route that minimizes total CO2 under a 10-day constraint. Return itinerary and an explanation of trade-offs."
    - Climate: "Ingest 30 rows of daily station temperatures (CSV, for simple tabular ingest). Create Station and Reading collections, then connect Stations with edges weighted by correlation of temperature time series. Detect 3 communities of stations with similar patterns and list exemplars."
    - Learning a lesson: "Design JSON Schemas for 'Concept', 'Exercise', 'Assessment'. Insert a mini-course on 'Bayes’ Theorem' with prerequisites. Traverse the prerequisite graph to propose a 90-minute learning path and generate 5 quiz questions, validating each against schema."
    - Course prep: "Build a knowledge graph for 'Intro to Graph Databases' (topics, readings, demos). Produce a 2-week syllabus ordered by dependency depth, and export demo datasets (collections + sample docs) to JSON for students."

- Augment (MCP-enabled coding)
  - Configuration options:
    - Settings UI: add a server named "ArangoDB" with Command `arango-server` (installed console script) or `python` with Args `["-m", "mcp_arangodb.entry"]`; set env vars as above.
    - Import JSON: in Augment settings, use "Import from JSON" with:
      ```json
      {
        "mcpServers": {
          "arangodb": {
            "command": "arango-server",
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
  - Coding and software engineering prompt ideas:
    - "Design JSON Schemas for 'User' and 'Session', migrate existing documents, and generate validation + insert flows (reject invalid)."
    - "Create DAOs/repositories for users and orders (Python examples) and show the AQL they would call via the MCP tools."
    - "Generate seed data for integration tests (20 users, 50 orders), bulk insert it, and provide cleanup steps."
    - "Profile slow AQL in 'orders' and propose indexes; then create those indexes and re-profile to confirm improvement."
    - "Back up critical collections to JSON, then demonstrate a selective restore into a fresh test database."
    - "Set up a health check and smoke-test script that calls 'list collections' and a trivial query for CI pipelines."
    - "Refactor a complex AQL into composable query-builder steps with filters, sorting, and pagination."
    - "Draft an HTTP API layer outline (endpoints and payloads) that maps to these MCP tools for a microservice."

---

 

## Appendix A: License Notes (ArangoDB)
- This repository’s code is released under the Apache License 2.0.
- Developed and tested primarily against ArangoDB 3.11.
- Starting with ArangoDB 3.12, the licensing model changed:
  - Source code: Business Source License 1.1 (BUSL-1.1). See official release notes:
    - https://docs.arangodb.com/3.12/release-notes/version-3.12/incompatible-changes-in-3-12/
  - Community binaries: ArangoDB Community License with usage limits:
    - https://arangodb.com/community-license/
  - Typical BSL model: source-available with usage restrictions until a change date, after which the code reverts to Apache 2.0. Verify the exact terms for your build and distribution.

Nothing in this repository grants rights to ArangoDB binaries; you must comply with ArangoDB’s license for the version you deploy.

## Appendix B: Python File Index

- mcp_arangodb/__init__.py — Package exports for the public API (e.g., Config, helpers).
- mcp_arangodb/__main__.py — CLI entrypoint for quick checks; run via `python -m mcp_arangodb`.
- mcp_arangodb/backup.py — Backup utilities (validate output dir; export collections to JSON).
- mcp_arangodb/config.py — Configuration loader/validator (env + optional .env via python-dotenv).
- mcp_arangodb/db.py — DB client and database acquisition, health checks, connection helpers.
- mcp_arangodb/entry.py — MCP stdio server bootstrap: lifecycle, tool registration, routing.
- mcp_arangodb/handlers.py — Tool implementations (CRUD, indexes, graphs, validation, queries).
- mcp_arangodb/models.py — Pydantic models for tool inputs and JSON Schemas for tool metadata.
- mcp_arangodb/schemas.py — Placeholder for reusable JSON Schemas and schema utilities.
- mcp_arangodb/server.py — Placeholder for future programmatic server orchestration utilities.
- mcp_arangodb/tools.py — Centralized tool-name constants used across the server.
- mcp_arangodb/types.py — TypedDicts/aliases maintained for typing and compatibility.

- scripts/inspector.py — Lightweight script for inspecting/diagnosing MCP I/O or environments.
- scripts/mcp_stdio_client.py — Simple MCP stdio client for manual testing and demos.

---

## References
- Source code: `mcp_arangodb/` (`entry.py`, `handlers.py`, `tools.py`)
- Setup script: `scripts/setup-arango.ps1`
- Docker Compose: `docker-compose.yml`
- [MCP specification](https://modelcontextprotocol.io/)
- [Python Arango driver](https://github.com/ArangoDB-Community/python-arango)
- [ArangoDB docs](https://www.arangodb.com/docs/)
- [Windows PowerShell](https://learn.microsoft.com/powershell/)
