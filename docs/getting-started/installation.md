# Installation Guide

Complete guide to installing ArangoDB 3.11 with Docker and configuring the mcp-arangodb-async server.

**Audience:** End Users (new to the project)  
**Prerequisites:** Docker Desktop installed, basic command-line familiarity  
**Estimated Time:** 15-20 minutes

---

## Table of Contents

1. [Why ArangoDB 3.11?](#why-arangodb-311)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

---

## Why ArangoDB 3.11?

### Licensing Considerations

⚠️ **IMPORTANT:** This project uses **ArangoDB 3.11**, the last version with the **Apache License 2.0**.

**Version Comparison:**

| Version | License | Implications |
|---------|---------|--------------|
| **ArangoDB 3.11** | Apache 2.0 | ✅ Permissive, production-ready, no restrictions |
| **ArangoDB 3.12+** | Business Source License 1.1 (BUSL-1.1) | ⚠️ Restrictions on commercial use, converts to Apache 2.0 after 4 years |

**Why This Matters:**
- **Apache 2.0** allows unrestricted commercial use
- **BUSL-1.1** restricts certain commercial deployments (see [ArangoDB Licensing FAQ](https://www.arangodb.com/subscriptions/license-faq/))
- **Version 3.11** is stable, production-ready, and fully supported by this project

**Key Takeaway:** Use ArangoDB 3.11 for maximum licensing flexibility.

### Technical Benefits

**ArangoDB 3.11 Features:**
- Multi-model database (document, graph, key-value)
- Native graph engine with traversal optimization
- AQL (ArangoDB Query Language) for complex queries
- ACID transactions
- Horizontal scalability (clustering)
- Full-text search
- Geospatial queries

**Why Docker?**
- **Isolation:** No conflicts with host system
- **Reproducibility:** Same environment across all machines
- **Easy reset:** Recreate clean instances instantly
- **Portability:** Works on Windows, macOS, Linux
- **Health checks:** Built-in readiness validation

---

## Prerequisites

### Required Software

**1. Docker Desktop**
- **Windows:** [Download Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
- **macOS:** [Download Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)
- **Linux:** [Install Docker Engine](https://docs.docker.com/engine/install/)

**Minimum Requirements:**
- 4 GB RAM allocated to Docker
- 10 GB free disk space
- WSL 2 backend (Windows)

**2. Python 3.11+**
- **Windows:** [Download Python](https://www.python.org/downloads/)
- **macOS:** `brew install python@3.11`
- **Linux:** `sudo apt install python3.11` (Ubuntu/Debian)

**3. Git (Optional)**
- For cloning the repository
- Alternative: Download ZIP from GitHub

### Verify Prerequisites

```powershell
# Check Docker
docker --version
# Expected: Docker version 20.x or higher

# Check Docker Compose
docker compose version
# Expected: Docker Compose version v2.x or higher

# Check Python
python --version
# Expected: Python 3.11.x or higher

# Check pip
python -m pip --version
# Expected: pip 23.x or higher
```

---

## Installation Steps

### Step 1: Clone Repository

```powershell
git clone https://github.com/PCfVW/mcp-arangodb-async.git
cd mcp-arangodb-async
```

**Alternative (Download ZIP):**
1. Visit https://github.com/PCfVW/mcp-arangodb-async
2. Click "Code" → "Download ZIP"
3. Extract to desired location
4. Open terminal in extracted folder

---

### Step 2: Install Python Dependencies

```powershell
python -m pip install -r requirements.txt
```

**What Gets Installed:**
- `python-arango==8.1.3` - Official ArangoDB driver
- `mcp>=1.0.0` - Model Context Protocol SDK
- `pydantic>=2.0.0` - Data validation
- `python-dotenv` - Environment variable management
- `starlette` - HTTP transport support (optional)

**Verify Installation:**
```powershell
python -c "import arango; print(arango.__version__)"
# Expected: 8.1.3
```

---

### Alternative: Docker Installation

Instead of installing Python dependencies locally, build the MCP server Docker image for environment isolation and reproducibility.

#### Build the Docker Image

```powershell
docker build -t mcp-arangodb-async:latest .
```

**What This Does:**
- Uses multi-stage build to minimize image size (~200MB final image)
- Installs all Python dependencies in isolated environment
- Creates non-root user for security
- Configures health checks for container monitoring

**Verify Build:**
```powershell
docker images mcp-arangodb-async

# Expected output:
# REPOSITORY              TAG       IMAGE ID       CREATED         SIZE
# mcp-arangodb-async      latest    abc123def456   2 minutes ago   ~200MB
```

#### Deployment Options

The Docker image supports 4 deployment modes via docker-compose profiles:

| Profile | Transport | Use Case | Command |
|---------|-----------|----------|---------|
| **stdio** | stdio | Desktop clients (Claude, Augment) | `docker compose --profile stdio up -d` |
| **http** | HTTP | Web clients, remote access | `docker compose --profile http up -d` |
| *(none)* | - | ArangoDB only | `docker compose up -d` |

**Usage Guides:**
- **stdio + Docker:** [Quickstart Guide - Docker Container](./quickstart-stdio.md#alternative-using-docker-container)
- **HTTP + Docker:** [Transport Configuration - HTTP with Docker](../configuration/transport-configuration.md#http-transport-with-docker)

---

### Step 3: Start ArangoDB Container

#### 3.1 Review docker-compose.yml

The project includes a pre-configured `docker-compose.yml`:

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

**Key Configuration:**
- **Image:** `arangodb:3.11` (Apache 2.0 licensed)
- **Port:** 8529 (ArangoDB default)
- **Root Password:** `changeme` (override with environment variable)
- **Persistent Data:** `arango_data` volume preserves data across restarts
- **Health Check:** Ensures database is ready before accepting connections

#### 3.2 Start Container

```powershell
docker compose up -d
```

**Expected Output:**
```
[+] Running 2/2
 ✔ Volume "mcp-arangodb-async_arango_data"  Created
 ✔ Container mcp_arangodb_test              Started
```

#### 3.3 Verify Container Health

```powershell
docker compose ps
```

**Expected Output:**
```
NAME                 STATUS              PORTS
mcp_arangodb_test    Up (healthy)        0.0.0.0:8529->8529/tcp
```

⚠️ **Wait for "healthy" status** (usually 10-15 seconds).

**Check Logs (if needed):**
```powershell
docker compose logs arangodb
```

---

### Step 4: Initialize Database

#### 4.1 Run Setup Script

```powershell
scripts\setup-arango.ps1 -RootPassword "changeme" -DbName "mcp_arangodb_test" -User "mcp_arangodb_user" -Password "mcp_arangodb_password" -Seed
```

**Parameters:**
- `-RootPassword` - ArangoDB root password (must match docker-compose.yml)
- `-DbName` - Database name to create
- `-User` - Application user to create
- `-Password` - Application user password
- `-Seed` - (Optional) Insert sample data for testing

**What This Does:**
1. Connects to ArangoDB as root
2. Creates database `mcp_arangodb_test`
3. Creates user `mcp_arangodb_user` with read/write permissions
4. Grants access to the database
5. (Optional) Seeds sample collections and data

**Expected Output:**
```
✓ Connected to ArangoDB
✓ Created database: mcp_arangodb_test
✓ Created user: mcp_arangodb_user
✓ Granted permissions
✓ Seeded sample data (3 collections, 50 documents)
```

#### 4.2 Verify Database Creation

**Option 1: Web UI**
1. Open http://localhost:8529 in browser
2. Login with `root` / `changeme`
3. Verify `mcp_arangodb_test` database exists
4. Check user `mcp_arangodb_user` in Users section

**Option 2: Command Line**
```powershell
curl -u root:changeme http://localhost:8529/_api/database
```

**Expected:** JSON response including `"mcp_arangodb_test"` in result array.

---

### Step 5: Configure Environment

#### 5.1 Create .env File

```powershell
Copy-Item env.example .env
notepad .env
```

#### 5.2 Edit Configuration

```dotenv
# ArangoDB Connection
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
ARANGO_TIMEOUT_SEC=30.0

# MCP Transport
MCP_TRANSPORT=stdio

# Toolset Configuration
MCP_COMPAT_TOOLSET=full

# Logging (Optional)
LOG_LEVEL=INFO
```

**Configuration Explained:**

| Variable | Description | Default |
|----------|-------------|---------|
| `ARANGO_URL` | Database connection endpoint | `http://localhost:8529` |
| `ARANGO_DB` | Target database name | `mcp_arangodb_test` |
| `ARANGO_USERNAME` | Authentication username | `mcp_arangodb_user` |
| `ARANGO_PASSWORD` | Authentication password | (required) |
| `ARANGO_TIMEOUT_SEC` | Connection timeout | `30.0` |
| `MCP_TRANSPORT` | Transport type (stdio or http) | `stdio` |
| `MCP_COMPAT_TOOLSET` | Tool availability (baseline or full) | `full` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

---

## Verification

### Health Check

```powershell
python -m mcp_arangodb_async --health
```

**Expected Output:**
```json
{"ok": true, "db": "mcp_arangodb_test", "user": "mcp_arangodb_user"}
```

✅ **Success!** Installation is complete.

### Test Server Startup

```powershell
python -m mcp_arangodb_async
```

**Expected Output:**
```
INFO:mcp_arangodb_async:Starting MCP server (stdio transport)
INFO:mcp_arangodb_async:Connected to ArangoDB: mcp_arangodb_test
INFO:mcp_arangodb_async:Registered 34 tools
```

Press `Ctrl+C` to stop the server.

---

## Troubleshooting

### Docker Container Won't Start

**Symptom:** `docker compose up -d` fails

**Solutions:**
1. Check Docker Desktop is running
2. Verify port 8529 is not in use: `netstat -ano | findstr :8529`
3. Check Docker logs: `docker compose logs arangodb`
4. Increase Docker memory allocation (Settings → Resources)

### Health Check Fails

**Symptom:** `python -m mcp_arangodb_async --health` returns error

**Solutions:**
1. Verify container is healthy: `docker compose ps`
2. Check credentials in `.env` match setup script
3. Test database connection: `curl http://localhost:8529`
4. Review ArangoDB logs: `docker compose logs arangodb`

### Setup Script Fails

**Symptom:** `setup-arango.ps1` reports error

**Solutions:**
1. Verify root password matches docker-compose.yml
2. Check container is running and healthy
3. Ensure PowerShell execution policy allows scripts: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
4. Run script with verbose output: `scripts\setup-arango.ps1 -Verbose`

---

## Next Steps

✅ **Installation Complete!**

**Continue Your Journey:**
- [Quickstart Guide (stdio)](quickstart-stdio.md) - Configure MCP client and test connectivity
- [First Interaction Guide](first-interaction.md) - Test prompts and AI-Coding examples
- [Transport Configuration](../configuration/transport-configuration.md) - Advanced transport options
- [Tools Reference](../user-guide/tools-reference.md) - Complete tool documentation

---

## Related Documentation
- [Quickstart Guide (stdio)](quickstart-stdio.md)
- [First Interaction Guide](first-interaction.md)
- [Transport Configuration](../configuration/transport-configuration.md)
- [Environment Variables](../configuration/environment-variables.md)
- [Troubleshooting](../user-guide/troubleshooting.md)

