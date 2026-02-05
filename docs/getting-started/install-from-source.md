# Install from Source

Guide for developers and contributors to install mcp-arangodb-async from source with Docker deployment options.

**Audience:** Developers, Contributors  
**Prerequisites:** Git, Python 3.11+, Docker Desktop (for Docker deployment)  
**Estimated Time:** 15-20 minutes

---

## Table of Contents

1. [When to Use This Guide](#when-to-use-this-guide)
2. [Clone and Install](#clone-and-install)
3. [Development Setup](#development-setup)
4. [Docker Deployment](#docker-deployment)
5. [Running Tests](#running-tests)
6. [Troubleshooting](#troubleshooting)

---

## When to Use This Guide

Use this guide if you:

- Want to contribute to the project
- Need to modify the source code
- Want to run the MCP server in Docker
- Need access to development tools and tests

**For most users:** The [Quickstart Guide](quickstart.md) with PyPI installation is simpler and recommended.

---

## Clone and Install

### Step 1: Clone the Repository

```powershell
git clone https://github.com/PCfVW/mcp-arangodb-async.git
cd mcp-arangodb-async
```

**Alternative (Download ZIP):**

1. Visit <https://github.com/PCfVW/mcp-arangodb-async>
2. Click "Code" → "Download ZIP"
3. Extract to desired location

### Step 2: Install the Package

```powershell
python -m pip install .
```

**For Development (Editable Install):**

```powershell
python -m pip install -e ".[dev]"
```

This installs the package in editable mode with development dependencies.

### Step 3: Verify Installation

```powershell
maa --version
```

---

## Development Setup

### Environment Configuration

Copy the example environment file:

```powershell
Copy-Item env.example .env
```

Edit `.env` with your ArangoDB settings:

```dotenv
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
```

### Start ArangoDB

The repository includes a docker-compose.yml with ArangoDB configuration:

```powershell
docker compose up arangodb -d
```

### Initialize Database

```powershell
$env:ARANGO_ROOT_PASSWORD = "changeme"
$env:MCP_USER_PASSWORD = "mcp_arangodb_password"

maa db add mcp_arangodb_test `
  --url http://localhost:8529 `
  --database mcp_arangodb_test `
  --username root `
  --password-env ARANGO_ROOT_PASSWORD `
  --with-user mcp_arangodb_user `
  --arango-password-env MCP_USER_PASSWORD
```

### Verify Setup

```powershell
maa --health
```

---

## Docker Deployment

Build and run the MCP server in Docker for isolation and reproducibility.

### Build the Docker Image

```powershell
docker build -t mcp-arangodb-async:latest .
```

**Verify Build:**

```powershell
docker images mcp-arangodb-async
```

### Deployment Profiles

The docker-compose.yml supports multiple deployment profiles:

| Profile | Transport | Use Case | Command |
|---------|-----------|----------|---------|
| *(none)* | - | ArangoDB only | `docker compose up -d` |
| **stdio** | stdio | Desktop clients | `docker compose --profile stdio up -d` |
| **http** | HTTP | Web clients | `docker compose --profile http up -d` |

### stdio Deployment

For desktop clients like Claude Desktop to use the Docker container:

```json
{
  "mcpServers": {
    "arangodb": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "--name", "mcp-arangodb-async-stdio",
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

**Note:** Use `host.docker.internal` to connect to ArangoDB running on the host machine.

### HTTP Deployment

For web clients and remote access:

```powershell
docker compose --profile http up -d
```

**Verify Health:**

```powershell
curl http://localhost:8000/health
```

**Configure HTTP Clients:**

LM Studio:

```json
{
  "mcpServers": {
    "arangodb": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

Gemini CLI:

```json
{
  "mcpServers": {
    "arangodb": {
      "httpUrl": "http://localhost:8000/mcp"
    }
  }
}
```

### Environment File for Docker

Create `.env-docker` for Docker-specific settings:

```dotenv
ARANGO_URL=http://arangodb:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
MCP_HTTP_HOST=0.0.0.0
MCP_HTTP_PORT=8000
```

Use with:

```powershell
docker compose --profile http --env-file .env-docker up -d
```

---

## Running Tests

### Run All Tests

```powershell
pytest
```

### Run with Coverage

```powershell
pytest --cov=mcp_arangodb_async --cov-report=html
```

### Run Specific Tests

```powershell
pytest tests/test_tools.py -v
```

---

## Troubleshooting

### Build Fails

**Symptom:** Docker build fails

**Solutions:**

1. Check Docker Desktop is running
2. Verify Dockerfile exists in project root
3. Check for network issues pulling base image

### Container Can't Connect to ArangoDB

**Symptom:** Health check fails in Docker

**Solutions:**

1. Use `http://arangodb:8529` (Docker service name) when both containers are in the same compose
2. Use `http://host.docker.internal:8529` when ArangoDB runs on host
3. Check containers are on the same network: `docker network ls`

### Import Errors in Development

**Symptom:** `ModuleNotFoundError` when running from source

**Solutions:**

1. Use editable install: `pip install -e .`
2. Verify virtual environment is activated
3. Check Python path: `python -c "import sys; print(sys.path)"`

---

## Next Steps

- [First Interaction Guide](first-interaction.md) - Test prompts and examples
- [Transport Configuration](../configuration/transport-configuration.md) - Advanced transport options
- [Contributing Guide](../development/contributing.md) - How to contribute

---

## Related Documentation

- [Quickstart Guide](quickstart.md) - PyPI installation
- [ArangoDB Installation](install-arangodb.md) - Database setup
- [Transport Configuration](../configuration/transport-configuration.md)

