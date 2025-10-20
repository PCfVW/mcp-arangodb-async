# Environment Variables Reference

Complete reference for all environment variables used by mcp-arangodb-async.

**Audience:** End Users and Developers  
**Prerequisites:** Basic understanding of environment variables  
**Estimated Time:** 10-15 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [ArangoDB Connection Variables](#arangodb-connection-variables)
3. [MCP Transport Variables](#mcp-transport-variables)
4. [Connection Tuning Variables](#connection-tuning-variables)
5. [Logging Variables](#logging-variables)
6. [Configuration Methods](#configuration-methods)
7. [Examples](#examples)
8. [Related Documentation](#related-documentation)

---

## Overview

The mcp-arangodb-async server is configured entirely through environment variables. This approach provides:

✅ **Flexibility** - Different configurations for dev/staging/production  
✅ **Security** - Credentials never hardcoded in source  
✅ **Portability** - Same code runs in different environments  
✅ **Docker-Friendly** - Easy to configure in containers

### Variable Categories

| Category | Variables | Purpose |
|----------|-----------|---------|
| **ArangoDB Connection** | `ARANGO_*` | Database connection settings |
| **MCP Transport** | `MCP_*` | Transport type and HTTP configuration |
| **Connection Tuning** | `ARANGO_CONNECT_*`, `ARANGO_TIMEOUT_*` | Retry logic and timeouts |
| **Logging** | `LOG_LEVEL` | Logging verbosity |

---

## ArangoDB Connection Variables

### ARANGO_URL

**Description:** ArangoDB server URL

**Type:** String (URL)  
**Required:** Yes  
**Default:** `http://localhost:8529`

**Examples:**
```bash
# Local development
ARANGO_URL=http://localhost:8529

# Docker container (using service name)
ARANGO_URL=http://arangodb:8529

# Remote server
ARANGO_URL=https://db.example.com:8529

# Cluster coordinator
ARANGO_URL=http://coordinator1.cluster.local:8529
```

**Notes:**
- Must include protocol (`http://` or `https://`)
- Port is typically 8529 (ArangoDB default)
- For Docker Compose, use service name instead of `localhost`

---

### ARANGO_DB

**Description:** Database name to connect to

**Type:** String  
**Required:** Yes  
**Default:** `_system`

**Examples:**
```bash
# Test database
ARANGO_DB=mcp_arangodb_test

# Production database
ARANGO_DB=production_db

# System database (default)
ARANGO_DB=_system
```

**Notes:**
- Database must exist before connecting
- Use `_system` for administrative operations
- Recommended: Create dedicated database for MCP server

---

### ARANGO_USERNAME

**Description:** ArangoDB username for authentication

**Type:** String  
**Required:** Yes  
**Default:** `root`

**Examples:**
```bash
# Root user (development)
ARANGO_USERNAME=root

# Dedicated MCP user (recommended)
ARANGO_USERNAME=mcp_arangodb_user

# Read-only user
ARANGO_USERNAME=readonly_user
```

**Security Best Practices:**
- ✅ Create dedicated user with minimal permissions
- ✅ Use different credentials for dev/staging/production
- ❌ Avoid using `root` in production

---

### ARANGO_PASSWORD

**Description:** ArangoDB password for authentication

**Type:** String  
**Required:** Yes  
**Default:** `""` (empty string)

**Examples:**
```bash
# Development
ARANGO_PASSWORD=changeme

# Production (use secrets manager)
ARANGO_PASSWORD=${DB_PASSWORD}

# Docker secret
ARANGO_PASSWORD=$(cat /run/secrets/arango_password)
```

**Security Best Practices:**
- ✅ Use secrets manager in production (AWS Secrets Manager, HashiCorp Vault)
- ✅ Rotate passwords regularly
- ✅ Use strong passwords (16+ characters, mixed case, numbers, symbols)
- ❌ Never commit passwords to version control
- ❌ Never log passwords

---

### ARANGO_VERIFY_CERTIFICATE

**Description:** Verify SSL/TLS certificates for HTTPS connections

**Type:** Boolean  
**Required:** No  
**Default:** `true`

**Examples:**
```bash
# Production (verify certificates)
ARANGO_VERIFY_CERTIFICATE=true

# Development with self-signed cert
ARANGO_VERIFY_CERTIFICATE=false
```

**Notes:**
- Only relevant for `https://` URLs
- Set to `false` only for development with self-signed certificates
- Always use `true` in production

---

## MCP Transport Variables

### MCP_TRANSPORT

**Description:** Transport type for MCP server

**Type:** String (enum)  
**Required:** No  
**Default:** `stdio`  
**Options:** `stdio`, `http`

**Examples:**
```bash
# Desktop clients (Claude Desktop, Augment Code)
MCP_TRANSPORT=stdio

# Web applications, containerized deployments
MCP_TRANSPORT=http
```

**When to Use:**
- **stdio:** Desktop AI clients, local development
- **http:** Web applications, Kubernetes, Docker Compose, horizontal scaling

---

### MCP_HTTP_HOST

**Description:** Host address to bind HTTP server to

**Type:** String (IP address or hostname)  
**Required:** No (only for HTTP transport)  
**Default:** `0.0.0.0`

**Examples:**
```bash
# Bind to all interfaces (Docker, Kubernetes)
MCP_HTTP_HOST=0.0.0.0

# Bind to localhost only (local development)
MCP_HTTP_HOST=127.0.0.1

# Bind to specific interface
MCP_HTTP_HOST=192.168.1.100
```

**Security Notes:**
- `0.0.0.0` - Accepts connections from any network interface
- `127.0.0.1` - Only accepts local connections (more secure)
- Use reverse proxy (nginx, Traefik) for production

---

### MCP_HTTP_PORT

**Description:** Port number for HTTP server

**Type:** Integer  
**Required:** No (only for HTTP transport)  
**Default:** `8000`  
**Range:** `1-65535`

**Examples:**
```bash
# Default port
MCP_HTTP_PORT=8000

# Custom port
MCP_HTTP_PORT=9000

# Standard HTTP port (requires root/admin)
MCP_HTTP_PORT=80
```

**Notes:**
- Ports below 1024 require elevated privileges
- Ensure port is not already in use
- Use reverse proxy for standard ports (80, 443)

---

### MCP_HTTP_STATELESS

**Description:** Enable stateless mode for HTTP transport

**Type:** Boolean  
**Required:** No (only for HTTP transport)  
**Default:** `false`

**Examples:**
```bash
# Stateful mode (single instance)
MCP_HTTP_STATELESS=false

# Stateless mode (horizontal scaling)
MCP_HTTP_STATELESS=true
```

**When to Use:**
- **Stateful (`false`):** Single server instance, session persistence
- **Stateless (`true`):** Multiple server instances, load balancing, Kubernetes

**Trade-offs:**
- Stateful: Better performance, session state maintained
- Stateless: Horizontal scaling, no session affinity required

---

### MCP_HTTP_CORS_ORIGINS

**Description:** Allowed CORS origins for HTTP transport

**Type:** String (comma-separated list)  
**Required:** No (only for HTTP transport)  
**Default:** `*`

**Examples:**
```bash
# Allow all origins (development only)
MCP_HTTP_CORS_ORIGINS=*

# Single origin
MCP_HTTP_CORS_ORIGINS=https://myapp.com

# Multiple origins
MCP_HTTP_CORS_ORIGINS=https://app.example.com,https://admin.example.com

# Localhost for development
MCP_HTTP_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Security Notes:**
- ⚠️ `*` allows any origin - use only in development
- ✅ Specify exact origins in production
- ✅ Use HTTPS origins in production

---

## Connection Tuning Variables

### ARANGO_TIMEOUT_SEC

**Description:** Request timeout for ArangoDB operations

**Type:** Float (seconds)  
**Required:** No  
**Default:** `30.0`

**Examples:**
```bash
# Default timeout
ARANGO_TIMEOUT_SEC=30.0

# Longer timeout for complex queries
ARANGO_TIMEOUT_SEC=60.0

# Shorter timeout for fast operations
ARANGO_TIMEOUT_SEC=10.0
```

**Recommendations:**
- **Simple queries:** 10-30 seconds
- **Complex analytics:** 60-120 seconds
- **Bulk operations:** 120-300 seconds

---

### ARANGO_CONNECT_RETRIES

**Description:** Number of connection retry attempts at startup

**Type:** Integer  
**Required:** No  
**Default:** `3`

**Examples:**
```bash
# Default retries
ARANGO_CONNECT_RETRIES=3

# More retries for slow Docker startup
ARANGO_CONNECT_RETRIES=10

# No retries (fail fast)
ARANGO_CONNECT_RETRIES=1
```

**When to Increase:**
- Docker Compose with health checks (10-15 seconds startup)
- Kubernetes with init containers
- Network with high latency

---

### ARANGO_CONNECT_DELAY_SEC

**Description:** Delay between connection retry attempts

**Type:** Float (seconds)  
**Required:** No  
**Default:** `1.0`

**Examples:**
```bash
# Default delay
ARANGO_CONNECT_DELAY_SEC=1.0

# Longer delay for slow startup
ARANGO_CONNECT_DELAY_SEC=2.0

# Shorter delay for fast retry
ARANGO_CONNECT_DELAY_SEC=0.5
```

**Calculation:**
Total retry time = `ARANGO_CONNECT_RETRIES * ARANGO_CONNECT_DELAY_SEC`

Example: 10 retries × 1.0s = 10 seconds maximum wait

---

## Logging Variables

### LOG_LEVEL

**Description:** Logging verbosity level

**Type:** String (enum)  
**Required:** No  
**Default:** `INFO`  
**Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

**Examples:**
```bash
# Production (minimal logging)
LOG_LEVEL=INFO

# Development (detailed logging)
LOG_LEVEL=DEBUG

# Troubleshooting (verbose)
LOG_LEVEL=DEBUG

# Errors only
LOG_LEVEL=ERROR
```

**Log Levels Explained:**
- **DEBUG:** Detailed diagnostic information (connection attempts, query execution)
- **INFO:** General informational messages (startup, tool calls)
- **WARNING:** Warning messages (deprecated features, non-critical issues)
- **ERROR:** Error messages (failed operations, exceptions)
- **CRITICAL:** Critical errors (server shutdown, fatal errors)

**Performance Impact:**
- DEBUG: High overhead, use only for troubleshooting
- INFO: Minimal overhead, suitable for production
- WARNING/ERROR: Negligible overhead

---

## Configuration Methods

### Method 1: .env File (Recommended)

**Create `.env` file in project root:**
```bash
# .env
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
MCP_TRANSPORT=stdio
LOG_LEVEL=INFO
```

**Load automatically:**
```python
# Automatically loaded by python-dotenv
python -m mcp_arangodb_async
```

---

### Method 2: Shell Export

**Bash/Zsh:**
```bash
export ARANGO_URL=http://localhost:8529
export ARANGO_DB=mcp_arangodb_test
export ARANGO_USERNAME=mcp_arangodb_user
export ARANGO_PASSWORD=mcp_arangodb_password
python -m mcp_arangodb_async
```

**PowerShell:**
```powershell
$env:ARANGO_URL="http://localhost:8529"
$env:ARANGO_DB="mcp_arangodb_test"
$env:ARANGO_USERNAME="mcp_arangodb_user"
$env:ARANGO_PASSWORD="mcp_arangodb_password"
python -m mcp_arangodb_async
```

---

### Method 3: MCP Client Configuration

**Claude Desktop (`claude_desktop_config.json`):**
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

### Method 4: Docker Compose

**docker-compose.yml:**
```yaml
services:
  mcp-server:
    image: mcp-arangodb-async:latest
    environment:
      ARANGO_URL: http://arangodb:8529
      ARANGO_DB: mcp_arangodb_test
      ARANGO_USERNAME: mcp_arangodb_user
      ARANGO_PASSWORD: ${ARANGO_PASSWORD}
      MCP_TRANSPORT: http
      MCP_HTTP_HOST: 0.0.0.0
      MCP_HTTP_PORT: 8000
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
```

---

## Examples

### Development (stdio)

```bash
# .env
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=root
ARANGO_PASSWORD=changeme
MCP_TRANSPORT=stdio
LOG_LEVEL=DEBUG
ARANGO_CONNECT_RETRIES=3
ARANGO_CONNECT_DELAY_SEC=1.0
```

---

### Production (HTTP with TLS)

```bash
# .env
ARANGO_URL=https://db.example.com:8529
ARANGO_DB=production_db
ARANGO_USERNAME=mcp_prod_user
ARANGO_PASSWORD=${DB_PASSWORD}  # From secrets manager
ARANGO_VERIFY_CERTIFICATE=true
MCP_TRANSPORT=http
MCP_HTTP_HOST=127.0.0.1  # Behind reverse proxy
MCP_HTTP_PORT=8000
MCP_HTTP_STATELESS=true  # Horizontal scaling
MCP_HTTP_CORS_ORIGINS=https://app.example.com
LOG_LEVEL=INFO
ARANGO_TIMEOUT_SEC=60.0
ARANGO_CONNECT_RETRIES=5
ARANGO_CONNECT_DELAY_SEC=2.0
```

---

### Docker Development

```bash
# .env
ARANGO_URL=http://arangodb:8529  # Docker service name
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
MCP_TRANSPORT=http
MCP_HTTP_HOST=0.0.0.0
MCP_HTTP_PORT=8000
MCP_HTTP_STATELESS=false
MCP_HTTP_CORS_ORIGINS=*
LOG_LEVEL=DEBUG
ARANGO_CONNECT_RETRIES=10  # Docker startup delay
ARANGO_CONNECT_DELAY_SEC=1.0
```

---

## Related Documentation

- [Transport Configuration](transport-configuration.md)
- [Installation Guide](../getting-started/installation.md)
- [Troubleshooting](../user-guide/troubleshooting.md)
- [HTTP Transport](../developer-guide/http-transport.md)

