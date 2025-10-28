# Quickstart Guide: stdio Transport

Complete guide to getting the mcp-arangodb-async server running with stdio transport for Claude Desktop and Augment Code.

**Audience:** End Users (new to the project)  
**Prerequisites:** Docker Desktop installed, Python 3.11+, basic command-line familiarity  
**Estimated Time:** 15-20 minutes

---

## What You'll Accomplish

By the end of this guide, you will:
- Have ArangoDB 3.11 running in Docker
- Have the MCP server installed and configured
- Successfully connect from Claude Desktop or Augment Code
- Execute your first AQL query through the MCP interface

---

## Prerequisites

### Required Software
- **Docker Desktop** - For running ArangoDB 3.11
- **Python 3.11+** - For the MCP server
- **Claude Desktop** or **Augment Code** - MCP client

### Verify Prerequisites

```powershell
# Check Docker
docker --version
# Expected: Docker version 20.x or higher

# Check Python
python --version
# Expected: Python 3.11.x or higher
```

---

## Step 1: Clone and Install

### 1.1 Clone the Repository

```powershell
git clone https://github.com/PCfVW/mcp-arangodb-async.git
cd mcp-arangodb-async
```

### 1.2 Install Python Dependencies

```powershell
python -m pip install -r requirements.txt
```

**What This Does:**
- Installs `python-arango` 8.x (official ArangoDB driver)
- Installs `mcp` SDK for Model Context Protocol
- Installs `pydantic` for argument validation
- Installs other required dependencies

---

## Step 2: Start ArangoDB

### 2.1 Start the Container

```powershell
docker compose up -d
```

**What This Does:**
- Pulls `arangodb:3.11` image (if not already present)
- Starts ArangoDB container named `mcp_arangodb_test`
- Exposes port 8529 for database access
- Sets root password to `changeme` (default)

### 2.2 Verify Container Health

```powershell
docker compose ps
```

**Expected Output:**
```
NAME                 STATUS              PORTS
mcp_arangodb_test    Up (healthy)        0.0.0.0:8529->8529/tcp
```

⚠️ **Wait for "healthy" status** before proceeding (usually 10-15 seconds).

---

## Alternative: Using Docker Container

Instead of installing Python locally, run the MCP server in Docker for environment isolation.

**Note:** MCP hosts like Claude Desktop must control the container lifecycle to maintain stdio communication. There is probably no benefit to start the MCP server with stdio in Docker by yourself, except for testing the deployment itself.

### Option A: docker-compose stdio Profile (Recommended)

**Build the Docker Image:**
```powershell
docker build -t mcp-arangodb-async:latest .
```

**Start the stdio Server:**
```powershell
# Start stdio server
docker compose --profile stdio up -d

# Verify container is running
docker compose ps

# Expected output:
# NAME                 STATUS              PORTS
# mcp_server_stdio     Up                  -
```

**Configure Claude Desktop:**

Edit `%APPDATA%\Claude\claude_desktop_config.json` (Windows) or `~/.config/Claude/claude_desktop_config.json` (macOS/Linux):

```json
{
  "mcpServers": {
    "mcp_arangodb_async": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--name", "mcp_arangodb_async-stdio",
        "-e", "ARANGO_URL=http://host.docker.internal:8529",
        "-e", "ARANGO_DB=mcp_arangodb_test",
        "-e", "ARANGO_USERNAME=mcp_arangodb_user",
        "-e", "ARANGO_PASSWORD=mcp_arangodb_password",
        "mcp-arangodb-async:latest"
      ]
    }
  }
}
```

**What This Does:**
- Claude Desktop runs `docker run` with environment variables injected via `-e` flags
- Uses `host.docker.internal` to access ArangoDB running on the host machine
- The `--rm` flag removes the container when Claude Desktop stops

**Alternative Configuration with Environment File:**

Create `.env-docker-stdio` in your project directory:

```dotenv
ARANGO_URL=http://host.docker.internal:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
```

Then use:

```json
{
  "mcpServers": {
    "mcp_arangodb_async": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--name", "mcp_arangodb_async-stdio",
        "--env-file", "path/to/.env-docker-stdio",
        "mcp-arangodb-async:latest"
      ]
    }
  }
}
```

📖 **Environment Variables:** See [Environment Variables Guide](../configuration/environment-variables.md) for complete configuration options.

**Skip to Step 5** if using Docker (Steps 3-4 are for Python installation only).

---

## Step 3: Initialize Database

### 3.1 Run Setup Script

```powershell
scripts\setup-arango.ps1 -RootPassword "changeme" -DbName "mcp_arangodb_test" -User "mcp_arangodb_user" -Password "mcp_arangodb_password" -Seed
```

**What This Does:**
- Creates database `mcp_arangodb_test`
- Creates user `mcp_arangodb_user` with password `mcp_arangodb_password`
- Grants read/write permissions
- Seeds sample data (optional `-Seed` flag)

### 3.2 Verify Database Creation

```powershell
# List databases (requires curl or Invoke-WebRequest)
curl -u root:changeme http://localhost:8529/_api/database
```

**Expected:** JSON response including `"mcp_arangodb_test"` in the result array.

---

## Step 4: Configure Environment

### 4.1 Create .env File

```powershell
Copy-Item env.example .env
notepad .env
```

### 4.2 Edit .env Contents

```dotenv
# ArangoDB Connection
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
ARANGO_TIMEOUT_SEC=30.0

# MCP Transport (stdio is default)
MCP_TRANSPORT=stdio

# Optional: Toolset Configuration
MCP_COMPAT_TOOLSET=full
```

**Configuration Explained:**
- `ARANGO_URL` - Database connection endpoint
- `ARANGO_DB` - Target database name
- `ARANGO_USERNAME` / `ARANGO_PASSWORD` - Authentication credentials
- `MCP_TRANSPORT=stdio` - Use stdio transport (default for desktop clients)
- `MCP_COMPAT_TOOLSET=full` - Enable all 34 tools (default)

📖 **Environment Variables:** See [Environment Variables Guide](../configuration/environment-variables.md) for complete configuration options and alternative setup methods.

---

## Step 5: Verify Installation

### 5.1 Run Health Check

```powershell
python -m mcp_arangodb_async --health
```

**Expected Output:**
```json
{"ok": true, "db": "mcp_arangodb_test", "user": "mcp_arangodb_user"}
```

✅ **Success!** The server can connect to ArangoDB.

❌ **If you see an error:**
- Check Docker container is running: `docker compose ps`
- Verify credentials in `.env` match setup script parameters
- Check ArangoDB logs: `docker compose logs arangodb`

---

## Step 6: Configure MCP Client

### Option A: Claude Desktop

**Location:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

**Add this server entry:**
```json
{
  "mcpServers": {
    "mcp_arangodb_async": {
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

**Restart Claude Desktop** after saving the configuration.

### Option B: Augment Code

**Settings UI:**
1. Open Augment Code settings
2. Navigate to MCP Servers section
3. Add new server:
   - **Name:** ArangoDB
   - **Command:** `python`
   - **Args:** `["-m", "mcp_arangodb_async"]`
   - **Environment:** Same as Claude Desktop above

**Import JSON:**
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

---

## Step 7: First Interaction

### 7.1 Test Basic Functionality

**Prompt:** "List all collections in my database."

**Expected Behavior:**
- Claude/Augment calls `arango_list_collections` tool
- Returns list of collection names (e.g., `["tests", "users", "products"]`)

### 7.2 Test Write Operation

**Prompt:** "Use arango_insert to add a document with name='test_document' and value=1 to a collection named 'tests'."

**Expected Behavior:**
- Creates `tests` collection if it doesn't exist
- Inserts document `{"name": "test_document", "value": 1}`
- Returns document with `_key`, `_id`, `_rev` fields

### 7.3 Test Graph Operation

**Prompt:** "Create a simple graph with users and follows relationships, then traverse from a specific user."

**Expected Behavior:**
- Creates graph with vertex and edge collections
- Inserts sample vertices and edges
- Performs traversal and returns connected nodes

---

## Troubleshooting

### Server Won't Start

**Symptom:** `python -m mcp_arangodb_async` fails immediately

**Solutions:**
1. Check Python version: `python --version` (must be 3.11+)
2. Reinstall dependencies: `python -m pip install -r requirements.txt --force-reinstall`
3. Check for port conflicts: `netstat -ano | findstr :8529`

### Connection Refused

**Symptom:** Health check fails with connection error

**Solutions:**
1. Verify Docker container is running: `docker compose ps`
2. Check ArangoDB logs: `docker compose logs arangodb`
3. Verify port 8529 is accessible: `curl http://localhost:8529`

### Authentication Failed

**Symptom:** Health check fails with "unauthorized" error

**Solutions:**
1. Verify credentials in `.env` match setup script
2. Re-run setup script with correct parameters
3. Check user permissions in ArangoDB web UI: http://localhost:8529

---

## Next Steps

✅ **You're ready to use the MCP server!**

**Learn More:**
- [First Interaction Guide](first-interaction.md) - Detailed test prompts and examples
- [Installation Guide](installation.md) - Advanced installation options
- [Tools Reference](../user-guide/tools-reference.md) - Complete tool documentation
- [Troubleshooting](../user-guide/troubleshooting.md) - Common issues and solutions

---

## Related Documentation
- [Installation Guide](installation.md)
- [First Interaction Guide](first-interaction.md)
- [Transport Configuration](../configuration/transport-configuration.md)
- [Environment Variables](../configuration/environment-variables.md)
- [Tools Reference](../user-guide/tools-reference.md)

