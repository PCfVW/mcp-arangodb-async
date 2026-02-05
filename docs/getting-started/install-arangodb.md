# ArangoDB Installation Guide

Complete guide to installing ArangoDB 3.11 as a prerequisite for mcp-arangodb-async.

**Audience:** All Users  
**Prerequisites:** Docker Desktop installed (recommended) or native installation  
**Estimated Time:** 10-15 minutes

---

## Table of Contents

1. [Why ArangoDB 3.11?](#why-arangodb-311)
2. [Option 1: Docker Installation (Recommended)](#option-1-docker-installation-recommended)
3. [Option 2: Native Installation](#option-2-native-installation)
4. [Initialize Database](#initialize-database)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## Why ArangoDB 3.11?

### Licensing Considerations

⚠️ **IMPORTANT:** This project uses **ArangoDB 3.11**, the last version with the **Apache License 2.0**.

| Version | License | Implications |
|---------|---------|--------------|
| **ArangoDB 3.11** | Apache 2.0 | ✅ Permissive, production-ready, no restrictions |
| **ArangoDB 3.12+** | Business Source License 1.1 (BUSL-1.1) | ⚠️ Restrictions on commercial use |

**Key Takeaway:** Use ArangoDB 3.11 for maximum licensing flexibility.

### Technical Benefits

- Multi-model database (document, graph, key-value)
- Native graph engine with traversal optimization
- AQL (ArangoDB Query Language) for complex queries
- ACID transactions and horizontal scalability

---

## Docker Installation

### Prerequisites

- **Docker Desktop** installed and running
- 4 GB RAM allocated to Docker
- 10 GB free disk space

**Verify Docker is available:**
```powershell
docker --version
docker compose version
```

### Step 1: Create Docker Compose File

Create a file named `docker-compose.yml` in your working directory:

```yaml
services:
  arangodb:
    image: arangodb:3.11
    environment:
      ARANGO_ROOT_PASSWORD: ${ARANGO_ROOT_PASSWORD:-your-secure-password}
    ports:
      - "${ARANGO_PORT:-8529}:8529"
    volumes:
      - arangodb_data:/var/lib/arangodb3
      - arangodb_apps:/var/lib/arangodb3-apps
    healthcheck:
      test: >
        arangosh --server.username root 
        --server.password "$ARANGO_ROOT_PASSWORD" 
        --javascript.execute-string "require('@arangodb').db._version()" 
        > /dev/null 2>&1 || exit 1
      interval: 5s
      timeout: 2s
      retries: 30
    restart: unless-stopped

volumes:
  arangodb_data:
    driver: local
  arangodb_apps:
    driver: local
```

### Step 2: Create Environment File

Create a `.arangodb-launch.env` file in the same directory:

```dotenv
# ArangoDB root password (change in production!)
ARANGO_ROOT_PASSWORD=your-secure-password

# Optional: Custom port if 8529 is in use
# ARANGO_PORT=8530
```

### Step 3: Start ArangoDB

```bash
docker compose --env-file .arangodb-launch.env up arangodb -d
```

**Expected Output:**
```
[+] Running 2/2
 ✔ Volume "arangodb_data"  Created
 ✔ Container arangodb-1    Started
```

### Step 4: Wait for Healthy Status

```powershell
docker compose ps
```

**Expected Output:**
```
NAME           STATUS              PORTS
arangodb-1     Up (healthy)        0.0.0.0:8529->8529/tcp
```

⚠️ **Wait for "healthy" status** (usually 10-15 seconds) before proceeding.

---

## Initialize Database

After ArangoDB is running, create a database and user for the MCP server.

### Using Admin CLI (Recommended)

If you have `mcp-arangodb-async` installed:

```powershell
# Set environment variables
$env:ARANGO_ROOT_PASSWORD = "changeme"
$env:ARANGO_PASSWORD = "mcp_arangodb_password"

# Create database with user
maa db add mcp_arangodb_test `
  --url http://localhost:8529 `
  --with-user mcp_arangodb_user `
  --arango-password-env ARANGO_PASSWORD
```

### Using ArangoDB Web UI

1. Open http://localhost:8529 in your browser
2. Login with `root` / `changeme`
3. Create database: Databases → Add Database → Name: `mcp_arangodb_test`
4. Create user: Users → Add User → Username: `mcp_arangodb_user`, Password: `mcp_arangodb_password`
5. Grant permissions: Users → `mcp_arangodb_user` → Permissions → Set `mcp_arangodb_test` to "Read/Write"

---

## Verification

### Test API Access

```powershell
curl http://localhost:8529/_api/version
```

**Expected:** JSON response with ArangoDB version information.

### Test Database Access

```powershell
curl -u root:changeme http://localhost:8529/_api/database
```

**Expected:** JSON response including your database name in the result array.

### Test User Authentication

```powershell
curl -u mcp_arangodb_user:mcp_arangodb_password http://localhost:8529/_db/mcp_arangodb_test/_api/version
```

**Expected:** Successful response (no authentication errors).

---

## Troubleshooting

### Docker Container Won't Start

**Symptom:** `docker compose up -d` fails

**Solutions:**
1. Check Docker Desktop is running
2. Verify port 8529 is not in use: `netstat -ano | findstr :8529`
3. Check Docker logs: `docker compose logs arangodb`
4. Increase Docker memory allocation (Settings → Resources)

### Container Not Becoming Healthy

**Symptom:** Container stays in "starting" status

**Solutions:**
1. Wait longer (initial startup can take 30+ seconds)
2. Check container logs: `docker compose logs arangodb`
3. Verify root password is set correctly in `.env`

### Connection Refused

**Symptom:** Cannot connect to http://localhost:8529

**Solutions:**
1. Verify container is running: `docker compose ps`
2. Check port mapping: `docker compose ps` should show `0.0.0.0:8529->8529/tcp`
3. Try explicit localhost: `curl http://127.0.0.1:8529/_api/version`

---

## Next Steps

✅ **ArangoDB is ready!**

Continue with the MCP server installation:
- [Quickstart Guide](quickstart.md) - Install from PyPI (recommended for most users)
- [Install from Source](install-from-source.md) - For developers and contributors

---

## Related Documentation
- [Quickstart Guide](quickstart.md)
- [Install from Source](install-from-source.md)
- [Environment Variables](../configuration/environment-variables.md)

