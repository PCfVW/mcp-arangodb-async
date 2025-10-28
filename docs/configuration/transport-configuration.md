# Transport Configuration

Detailed guide to configuring stdio and HTTP transports for the mcp-arangodb-async server.

**Audience:** End Users and Developers  
**Prerequisites:** Server installed, basic understanding of MCP transports  
**Estimated Time:** 20-30 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [stdio Transport Configuration](#stdio-transport-configuration)
3. [HTTP Transport Configuration](#http-transport-configuration)
4. [Environment Variables Reference](#environment-variables-reference)
5. [Client-Specific Configuration](#client-specific-configuration)
6. [Troubleshooting Transport Issues](#troubleshooting-transport-issues)
7. [Related Documentation](#related-documentation)

---

## Overview

The mcp-arangodb-async server supports two transport types:

| Transport | Configuration Method | Use Case |
|-----------|---------------------|----------|
| **stdio** | Client configuration file | Desktop AI clients (Claude Desktop, Augment Code) |
| **HTTP** | Environment variables + command-line args | Web applications, Docker deployments |

### Quick Start

**stdio (Default):**
```powershell
# No configuration needed - works out of the box
python -m mcp_arangodb_async
```

**HTTP:**
```powershell
# Set environment variable
$env:MCP_TRANSPORT="http"
python -m mcp_arangodb_async
```

---

## stdio Transport Configuration

### Overview

**stdio transport** uses standard input/output for communication. The client launches the server as a subprocess and communicates via JSON-RPC messages over stdin/stdout.

### Environment Variables

**Required:**
```dotenv
# ArangoDB connection (required)
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
```

**Optional:**
```dotenv
# Transport type (default: stdio)
MCP_TRANSPORT=stdio

# Connection timeout (default: 30.0 seconds)
ARANGO_TIMEOUT_SEC=30.0

# Toolset configuration (default: full)
MCP_COMPAT_TOOLSET=full

# Logging level (default: INFO)
LOG_LEVEL=INFO
```

### Client Configuration

#### Claude Desktop (Windows)

**Location:** `%APPDATA%\Claude\claude_desktop_config.json`

**Configuration:**
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

**Explanation:**
- `command`: Python executable (must be in PATH)
- `args`: Module to run (`-m mcp_arangodb_async`)
- `env`: Environment variables passed to subprocess

---

#### Claude Desktop (macOS/Linux)

**Location:** `~/.config/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "arangodb": {
      "command": "python3",
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

**Note:** Use `python3` instead of `python` on macOS/Linux.

---

#### Augment Code

**Location:** Augment Code settings (UI or configuration file)

**Configuration:**
```json
{
  "mcp": {
    "servers": {
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
}
```

---

#### Custom MCP Client

**Python Example:**
```python
import asyncio
import subprocess
import json

async def run_mcp_client():
    # Launch server as subprocess
    process = await asyncio.create_subprocess_exec(
        "python", "-m", "mcp_arangodb_async",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={
            "ARANGO_URL": "http://localhost:8529",
            "ARANGO_DB": "mcp_arangodb_test",
            "ARANGO_USERNAME": "mcp_arangodb_user",
            "ARANGO_PASSWORD": "mcp_arangodb_password",
        }
    )
    
    # Send JSON-RPC request
    request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 1
    }
    process.stdin.write(json.dumps(request).encode() + b'\n')
    await process.stdin.drain()
    
    # Read response
    response_line = await process.stdout.readline()
    response = json.loads(response_line.decode())
    print(response)
    
    # Cleanup
    process.terminate()
    await process.wait()

asyncio.run(run_mcp_client())
```

---

### Using Docker Container

Run the MCP server in Docker for environment isolation.

**Note:** MCP hosts like Claude Desktop must control the container lifecycle to maintain stdio communication.

**Claude Desktop Configuration:**
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

📖 **Complete Docker guide:** [Quickstart (stdio) - Docker Container](../getting-started/quickstart-stdio.md#alternative-using-docker-container)

---

### Verification

**Test stdio Transport:**
```powershell
# Start server manually (for testing)
python -m mcp_arangodb_async

# Server should start and wait for stdin
# Press Ctrl+C to stop
```

**Check Logs:**
```
INFO:mcp_arangodb_async:Starting MCP server (stdio transport)
INFO:mcp_arangodb_async:Connected to ArangoDB: mcp_arangodb_test
INFO:mcp_arangodb_async:Registered 34 tools
```

---

## HTTP Transport Configuration

### Overview

**HTTP transport** runs the server as a standalone HTTP service. Clients connect via HTTP POST requests and receive responses via Server-Sent Events (SSE).

### Environment Variables

**Required:**
```dotenv
# Transport type
MCP_TRANSPORT=http

# ArangoDB connection
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
```

**Optional:**
```dotenv
# HTTP server configuration
MCP_HTTP_HOST=0.0.0.0          # Bind address (0.0.0.0 = all interfaces)
MCP_HTTP_PORT=8000             # Port number
MCP_HTTP_STATELESS=false       # Stateless mode (true/false)
MCP_HTTP_CORS_ORIGINS=*        # CORS origins (comma-separated)

# Connection timeout
ARANGO_TIMEOUT_SEC=30.0

# Toolset configuration
MCP_COMPAT_TOOLSET=full

# Logging level
LOG_LEVEL=INFO
```

---

### Command-Line Arguments

**Start HTTP Server:**
```powershell
python -m mcp_arangodb_async --transport http
```

**With Custom Port:**
```powershell
python -m mcp_arangodb_async --transport http --port 9000
```

**With Custom Host:**
```powershell
python -m mcp_arangodb_async --transport http --host 127.0.0.1 --port 8000
```

**Stateless Mode:**
```powershell
python -m mcp_arangodb_async --transport http --stateless
```

**All Options:**
```powershell
python -m mcp_arangodb_async `
  --transport http `
  --host 0.0.0.0 `
  --port 8000 `
  --stateless
```

---

### Using Docker Container

Run the MCP server in Docker for isolation and reproducibility.

**Start HTTP Server:**
```powershell
# Start ArangoDB + MCP HTTP server
docker compose --profile http up -d

# Verify health endpoint
curl http://localhost:8000/health
```

**Using Environment File:**

Create `.env` file in project root:
```dotenv
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
MCP_HTTP_HOST=0.0.0.0
MCP_HTTP_PORT=8000
```

Then start with:
```powershell
docker compose --profile http --env-file .env up -d
```

**Client Configuration:**

**LM Studio:**
```json
{
  "mcpServers": {
    "mcp_arangodb_async": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

**Gemini CLI:**
```json
{
  "mcpServers": {
    "mcp_arangodb_async": {
      "httpUrl": "http://localhost:8000/mcp"
    }
  }
}
```

**Environment Configuration:** You can configure environment variables using inline `env` objects in MCP host configs, `-e` flags in Docker commands, or `--env-file` with environment files. See [Environment Variables Guide](environment-variables.md) for complete options.

---

## Environment Variables Reference

### Core Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MCP_TRANSPORT` | string | `stdio` | Transport type: `stdio` or `http` |
| `ARANGO_URL` | string | (required) | ArangoDB connection URL |
| `ARANGO_DB` | string | (required) | Database name |
| `ARANGO_USERNAME` | string | (required) | Authentication username |
| `ARANGO_PASSWORD` | string | (required) | Authentication password |
| `ARANGO_TIMEOUT_SEC` | float | `30.0` | Connection timeout in seconds |

---

### HTTP Transport Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MCP_HTTP_HOST` | string | `0.0.0.0` | Host address to bind to |
| `MCP_HTTP_PORT` | integer | `8000` | Port number to bind to |
| `MCP_HTTP_STATELESS` | boolean | `false` | Stateless mode (true/false) |
| `MCP_HTTP_CORS_ORIGINS` | string | `*` | CORS origins (comma-separated) |

**Host Binding Options:**
- `0.0.0.0` - Bind to all network interfaces (accessible from network)
- `127.0.0.1` - Bind to localhost only (local access only)
- Specific IP - Bind to specific network interface

**Stateless Mode:**
- `false` (default) - Stateful mode, maintains session state
- `true` - Stateless mode, no session state (required for horizontal scaling)

**CORS Origins:**
- `*` - Allow all origins (development only)
- `https://myapp.com` - Single origin
- `https://app1.com,https://app2.com` - Multiple origins (comma-separated)

---

### Optional Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MCP_COMPAT_TOOLSET` | string | `full` | Toolset: `baseline` (7 tools) or `full` (34 tools) |
| `LOG_LEVEL` | string | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

### Configuration Examples

#### Development (stdio)

**.env:**
```dotenv
MCP_TRANSPORT=stdio
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
LOG_LEVEL=DEBUG
```

---

#### Production (HTTP with TLS)

**.env:**
```dotenv
MCP_TRANSPORT=http
MCP_HTTP_HOST=127.0.0.1  # Bind to localhost (reverse proxy handles external access)
MCP_HTTP_PORT=8000
MCP_HTTP_STATELESS=true  # Stateless for horizontal scaling
MCP_HTTP_CORS_ORIGINS=https://myapp.com,https://app.example.com
ARANGO_URL=http://arangodb-cluster:8529
ARANGO_DB=production_db
ARANGO_USERNAME=prod_user
ARANGO_PASSWORD=${ARANGO_PASSWORD}  # From secrets manager
LOG_LEVEL=INFO
```

---

#### Docker Development

**.env:**
```dotenv
MCP_TRANSPORT=http
MCP_HTTP_HOST=0.0.0.0
MCP_HTTP_PORT=8000
MCP_HTTP_STATELESS=false
MCP_HTTP_CORS_ORIGINS=*
ARANGO_URL=http://arangodb:8529  # Docker service name
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
LOG_LEVEL=DEBUG
```

---

## Client-Specific Configuration

### Claude Desktop

**Configuration File Location:**
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

**Full Configuration:**
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
        "ARANGO_PASSWORD": "mcp_arangodb_password",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Restart Claude Desktop** after configuration changes.

---

### Augment Code

**Configuration Method:** UI settings or configuration file

**Steps:**
1. Open Augment Code settings
2. Navigate to MCP Servers section
3. Add new server:
   - **Name:** arangodb
   - **Command:** python
   - **Args:** -m mcp_arangodb_async
   - **Environment Variables:** (see below)

**Environment Variables:**
```
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
```

---

### Web Application (HTTP)

**JavaScript Client Example:**
```javascript
import { MCPClient } from '@modelcontextprotocol/sdk';

const client = new MCPClient({
  transport: 'http',
  url: 'http://localhost:8000/mcp',
  headers: {
    'Content-Type': 'application/json',
    // Add authentication if implemented
    // 'Authorization': 'Bearer YOUR_TOKEN'
  }
});

// Connect to server
await client.connect();

// List available tools
const tools = await client.listTools();
console.log('Available tools:', tools);

// Call a tool
const result = await client.callTool('arango_list_collections', {});
console.log('Collections:', result);

// Disconnect
await client.disconnect();
```

---

### Python Application (HTTP)

**Python Client Example:**
```python
import httpx
import json

class MCPHTTPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id = None

    async def list_tools(self):
        """List available tools."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 1
                },
                headers={"Mcp-Session-Id": self.session_id} if self.session_id else {}
            )

            # Extract session ID from response headers
            if "Mcp-Session-Id" in response.headers:
                self.session_id = response.headers["Mcp-Session-Id"]

            return response.json()

    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/mcp",
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": arguments
                    },
                    "id": 2
                },
                headers={"Mcp-Session-Id": self.session_id} if self.session_id else {}
            )
            return response.json()

# Usage
import asyncio

async def main():
    client = MCPHTTPClient("http://localhost:8000")

    # List tools
    tools = await client.list_tools()
    print("Available tools:", tools)

    # Call tool
    result = await client.call_tool("arango_list_collections", {})
    print("Collections:", result)

asyncio.run(main())
```

---

## Troubleshooting Transport Issues

### stdio Transport Issues

#### Issue 1: Server Not Starting in Claude Desktop

**Symptoms:**
- Server doesn't appear in Claude Desktop MCP servers list
- No error messages visible

**Solutions:**

**1. Check Python Installation:**
```powershell
python --version
# Should show Python 3.11 or higher
```

**2. Verify Module Installation:**
```powershell
python -m mcp_arangodb_async --health
# Should return JSON with database status
```

**3. Check Configuration File:**
- Verify file location: `%APPDATA%\Claude\claude_desktop_config.json`
- Validate JSON syntax (use JSON validator)
- Check command path (use full path if needed)

**4. Use Full Python Path:**
```json
{
  "mcpServers": {
    "arangodb": {
      "command": "C:\\Python311\\python.exe",
      "args": ["-m", "mcp_arangodb_async"]
    }
  }
}
```

---

#### Issue 2: Database Connection Errors

**Symptoms:**
- Server starts but tools return "DatabaseUnavailable" errors

**Solutions:**

**1. Verify ArangoDB is Running:**
```powershell
docker compose ps
# Should show arangodb container as "healthy"
```

**2. Test Database Connection:**
```powershell
curl http://localhost:8529/_api/version
# Should return ArangoDB version
```

**3. Check Credentials:**
```powershell
python -m mcp_arangodb_async --health
# Should return {"ok": true, ...}
```

**4. Review Server Logs:**
- Claude Desktop logs: `%APPDATA%\Claude\logs\`
- Look for connection errors

---

### HTTP Transport Issues

#### Issue 1: Port Already in Use

**Symptoms:**
```
Error: Address already in use: 0.0.0.0:8000
```

**Solutions:**

**1. Find Process Using Port:**
```powershell
netstat -ano | findstr :8000
```

**2. Kill Process:**
```powershell
taskkill /PID <PID> /F
```

**3. Use Different Port:**
```powershell
python -m mcp_arangodb_async --transport http --port 9000
```

---

#### Issue 2: CORS Errors

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/mcp' from origin 'https://myapp.com' has been blocked by CORS policy
```

**Solutions:**

**1. Add Origin to CORS Configuration:**
```dotenv
MCP_HTTP_CORS_ORIGINS=https://myapp.com
```

**2. Allow Multiple Origins:**
```dotenv
MCP_HTTP_CORS_ORIGINS=https://myapp.com,https://app.example.com
```

**3. Development Only - Allow All:**
```dotenv
MCP_HTTP_CORS_ORIGINS=*
```

⚠️ **Never use `*` in production!**

---

#### Issue 3: Health Check Fails

**Symptoms:**
```
curl http://localhost:8000/health
# Returns connection refused or timeout
```

**Solutions:**

**1. Verify Server is Running:**
```powershell
# Check if process is running
Get-Process | Where-Object {$_.ProcessName -like "*python*"}
```

**2. Check Logs:**
```powershell
# Server logs should show:
# INFO:mcp_arangodb_async:Starting MCP HTTP server on 0.0.0.0:8000
```

**3. Test with Verbose Logging:**
```powershell
$env:LOG_LEVEL="DEBUG"
python -m mcp_arangodb_async --transport http
```

**4. Verify Firewall Rules:**
```powershell
# Windows Firewall may block port 8000
# Add firewall rule or temporarily disable for testing
```

---

## Related Documentation
- [Transport Comparison](../architecture/transport-comparison.md)
- [Design Decisions](../architecture/design-decisions.md)
- [Environment Variables](environment-variables.md)
- [Quickstart Guide (stdio)](../getting-started/quickstart-stdio.md)
- [Troubleshooting](../user-guide/troubleshooting.md)
### Docker Configuration

**docker-compose.yml:**
```yaml
services:
  arangodb:
    image: arangodb:3.11
    container_name: mcp_arangodb_test
    environment:
      ARANGO_ROOT_PASSWORD: changeme
    ports:
      - "8529:8529"
    volumes:
      - arango_data:/var/lib/arangodb3
    healthcheck:
      test: arangosh --server.username root --server.password "changeme" --javascript.execute-string "require('@arangodb').db._version()" > /dev/null 2>&1 || exit 1
      interval: 5s
      timeout: 2s
      retries: 30
  
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      MCP_TRANSPORT: http
      MCP_HTTP_HOST: 0.0.0.0
      MCP_HTTP_PORT: 8000
      MCP_HTTP_STATELESS: "false"
      MCP_HTTP_CORS_ORIGINS: "*"
      ARANGO_URL: http://arangodb:8529
      ARANGO_DB: mcp_arangodb_test
      ARANGO_USERNAME: mcp_arangodb_user
      ARANGO_PASSWORD: mcp_arangodb_password
    depends_on:
      arangodb:
        condition: service_healthy
    healthcheck:
      test: curl -f http://localhost:8000/health || exit 1
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  arango_data:
```

**Start Services:**
```powershell
docker compose up -d
```

**Check Health:**
```powershell
curl http://localhost:8000/health
```

---

### Kubernetes Configuration

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-arangodb
  labels:
    app: mcp-arangodb
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-arangodb
  template:
    metadata:
      labels:
        app: mcp-arangodb
    spec:
      containers:
      - name: mcp-server
        image: mcp-arangodb-async:latest
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: MCP_TRANSPORT
          value: "http"
        - name: MCP_HTTP_HOST
          value: "0.0.0.0"
        - name: MCP_HTTP_PORT
          value: "8000"
        - name: MCP_HTTP_STATELESS
          value: "true"  # Required for horizontal scaling
        - name: ARANGO_URL
          value: "http://arangodb-service:8529"
        - name: ARANGO_DB
          valueFrom:
            secretKeyRef:
              name: arango-credentials
              key: database
        - name: ARANGO_USERNAME
          valueFrom:
            secretKeyRef:
              name: arango-credentials
              key: username
        - name: ARANGO_PASSWORD
          valueFrom:
            secretKeyRef:
              name: arango-credentials
              key: password
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-arangodb-service
spec:
  selector:
    app: mcp-arangodb
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: LoadBalancer
```

---

### Verification

**Health Check:**
```powershell
curl http://localhost:8000/health
```

**Expected Response:**
```json
{
  "ok": true,
  "db": "mcp_arangodb_test",
  "user": "mcp_arangodb_user",
  "version": "3.11.0"
}
```

**List Tools:**
```powershell
curl -X POST http://localhost:8000/mcp `
  -H "Content-Type: application/json" `
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 1
  }'
```

---


