# Troubleshooting Guide

Solutions for common issues with mcp-arangodb-async.

**Audience:** End Users  
**Prerequisites:** Basic understanding of MCP, ArangoDB, and Docker  
**Estimated Time:** 15-20 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [ArangoDB Connection Issues](#arangodb-connection-issues)
3. [MCP Client Issues](#mcp-client-issues)
4. [Transport Issues](#transport-issues)
5. [Tool Execution Errors](#tool-execution-errors)
6. [Performance Issues](#performance-issues)
7. [Docker Issues](#docker-issues)
8. [Getting Help](#getting-help)
9. [Related Documentation](#related-documentation)

---

## Overview

This guide provides solutions for common issues encountered when using mcp-arangodb-async. Each section includes:

- **Symptoms:** How to identify the issue
- **Causes:** Why the issue occurs
- **Solutions:** Step-by-step fixes
- **Prevention:** How to avoid the issue

---

## ArangoDB Connection Issues

### Issue 1: Connection Refused

**Symptoms:**
```
ConnectionError: [Errno 111] Connection refused
Error: Failed to connect to ArangoDB
```

**Causes:**
- ArangoDB container not running
- Wrong URL or port
- Firewall blocking connection

**Solutions:**

**1. Verify ArangoDB is running:**
```powershell
# Check container status
docker compose ps

# Should show "healthy" status
# If not running:
docker compose up -d arangodb
```

**2. Test connection directly:**
```powershell
curl http://localhost:8529/_api/version
```

**Expected response:**
```json
{"server":"arango","version":"3.11.x","license":"community"}
```

**3. Check port binding:**
```powershell
# Windows
netstat -ano | findstr :8529

# Linux/macOS
lsof -i :8529
```

**4. Verify environment variables:**
```powershell
python -m mcp_arangodb_async --health
```

**Prevention:**
- Use Docker health checks in `docker-compose.yml`
- Set `ARANGO_CONNECT_RETRIES=10` for Docker startup delays

---

### Issue 2: Authentication Failed

**Symptoms:**
```
ArangoError: [HTTP 401][ERR 11] not authorized to execute this request
Error: Authentication failed
```

**Causes:**
- Wrong username or password
- User doesn't have required permissions
- Database doesn't exist

**Solutions:**

**1. Verify credentials:**
```powershell
# Test with curl
curl -u root:changeme http://localhost:8529/_api/version
```

**2. Check user permissions:**
```powershell
# Access ArangoDB web UI
# http://localhost:8529
# Login and check user permissions in Users section
```

**3. Re-run setup script:**
```powershell
pwsh -File .\scripts\setup-arango.ps1 -RootPassword "changeme"
```

**4. Verify environment variables match:**
```powershell
# Check .env file
cat .env | findstr ARANGO

# Should match setup script parameters
```

**Prevention:**
- Store credentials in `.env` file
- Use consistent passwords across setup and configuration
- Document credentials in team password manager

---

### Issue 3: Database Not Found

**Symptoms:**
```
ArangoError: [HTTP 404][ERR 1228] database not found: mcp_arangodb_test
```

**Causes:**
- Database not created
- Wrong database name in configuration
- Setup script not run

**Solutions:**

**1. List existing databases:**
```powershell
curl -u root:changeme http://localhost:8529/_api/database
```

**2. Create database manually:**
```powershell
# Via web UI: http://localhost:8529
# Or via setup script:
pwsh -File .\scripts\setup-arango.ps1
```

**3. Verify ARANGO_DB environment variable:**
```bash
# Should match existing database name
ARANGO_DB=mcp_arangodb_test
```

**Prevention:**
- Run setup script after starting ArangoDB
- Use health check to verify database exists

---

### Issue 4: Timeout Errors

**Symptoms:**
```
TimeoutError: Request timed out after 30.0 seconds
ArangoError: [HTTP 408] Request timeout
```

**Causes:**
- Query too complex
- Large dataset
- Network latency
- Database overloaded

**Solutions:**

**1. Increase timeout:**
```bash
# .env
ARANGO_TIMEOUT_SEC=60.0
```

**2. Optimize query:**
```aql
# Add indexes for frequently queried fields
# Use LIMIT to reduce result size
# Avoid full collection scans
```

**3. Check database performance:**
```powershell
# Access web UI: http://localhost:8529
# Check Dashboard → Statistics
# Look for high CPU/memory usage
```

**Prevention:**
- Create appropriate indexes
- Use query profiling: `arango_query_profile` tool
- Monitor database performance

---

## MCP Client Issues

### Issue 1: Server Not Appearing in Claude Desktop

**Symptoms:**
- Server doesn't show in Claude Desktop MCP servers list
- No error messages visible

**Causes:**
- Configuration file syntax error
- Wrong file location
- Python not in PATH
- Module not installed

**Solutions:**

**1. Verify configuration file location:**
```powershell
# Windows
notepad %APPDATA%\Claude\claude_desktop_config.json

# macOS
open ~/.config/Claude/claude_desktop_config.json
```

**2. Validate JSON syntax:**
```powershell
# Use online JSON validator or:
python -m json.tool %APPDATA%\Claude\claude_desktop_config.json
```

**3. Test module directly:**
```powershell
python -m mcp_arangodb_async --health
```

**4. Check Python in PATH:**
```powershell
python --version
# Should show Python 3.11+

# If not found, use full path in config:
"command": "C:\\Python311\\python.exe"
```

**5. Restart Claude Desktop:**
```powershell
# Close Claude Desktop completely
# Reopen and check MCP servers list
```

**Prevention:**
- Use JSON validator before saving config
- Test module with `--health` flag before configuring client
- Keep Python in PATH

---

### Issue 2: Tools Return "Database Unavailable"

**Symptoms:**
```
Error: Database unavailable
Hint: Ensure ArangoDB is running
```

**Causes:**
- ArangoDB not running when server started
- Connection lost after startup
- Wrong credentials in client config

**Causes:**
- Environment variables not passed to subprocess
- ArangoDB started after MCP server

**Solutions:**

**1. Verify ArangoDB is running:**
```powershell
docker compose ps
# Should show "healthy"
```

**2. Check environment variables in config:**
```json
{
  "mcpServers": {
    "arangodb": {
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

**3. Restart MCP server:**
```powershell
# Restart Claude Desktop to restart server
```

**4. Check Claude Desktop logs:**
```powershell
# Windows
notepad %APPDATA%\Claude\logs\mcp-server-arangodb.log

# Look for connection errors
```

**Prevention:**
- Start ArangoDB before MCP client
- Use retry logic: `ARANGO_CONNECT_RETRIES=10`
- Enable lazy connection recovery (automatic)

---

### Issue 3: Tool Not Found

**Symptoms:**
```
Error: Tool 'arango_query' not found
Available tools: []
```

**Causes:**
- Server failed to start
- Tool registration failed
- Wrong toolset configuration

**Solutions:**

**1. Check server logs:**
```powershell
# Claude Desktop logs
%APPDATA%\Claude\logs\
```

**2. Test tool listing:**
```powershell
python scripts/mcp_stdio_client.py
# Should list all 34 tools
```

**3. Verify toolset configuration:**
```bash
# .env
MCP_COMPAT_TOOLSET=full  # Not baseline
```

**Prevention:**
- Always use `MCP_COMPAT_TOOLSET=full`
- Test with `mcp_stdio_client.py` before using in Claude

---

## Transport Issues

### Issue 1: stdio Transport - Server Crashes

**Symptoms:**
```
Server process exited with code 1
Connection lost
```

**Causes:**
- Unhandled exception
- Python version incompatibility
- Missing dependencies

**Solutions:**

**1. Check Python version:**
```powershell
python --version
# Must be 3.11 or 3.12
```

**2. Reinstall dependencies:**
```powershell
python -m pip install -r requirements.txt --force-reinstall
```

**3. Test with verbose logging:**
```bash
# .env
LOG_LEVEL=DEBUG
```

**4. Check for import errors:**
```powershell
python -c "import mcp_arangodb_async; print('OK')"
```

**Prevention:**
- Use Python 3.11 or 3.12
- Install in virtual environment
- Pin dependency versions

---

### Issue 2: HTTP Transport - Port Already in Use

**Symptoms:**
```
OSError: [Errno 48] Address already in use: 0.0.0.0:8000
Error: Failed to bind to port 8000
```

**Causes:**
- Another process using port 8000
- Previous server instance still running

**Solutions:**

**1. Find process using port:**
```powershell
# Windows
netstat -ano | findstr :8000

# Linux/macOS
lsof -i :8000
```

**2. Kill process:**
```powershell
# Windows (use PID from netstat)
taskkill /PID <PID> /F

# Linux/macOS
kill -9 <PID>
```

**3. Use different port:**
```bash
# .env
MCP_HTTP_PORT=9000
```

**Prevention:**
- Use unique port for each service
- Implement graceful shutdown
- Use process manager (systemd, supervisor)

---

### Issue 3: HTTP Transport - CORS Errors

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/mcp' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```

**Causes:**
- Origin not in allowed list
- Missing CORS headers
- Wrong CORS configuration

**Solutions:**

**1. Add origin to allowed list:**
```bash
# .env
MCP_HTTP_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

**2. Allow all origins (development only):**
```bash
# .env
MCP_HTTP_CORS_ORIGINS=*
```

**3. Verify CORS headers:**
```powershell
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -X OPTIONS \
     http://localhost:8000/mcp
```

**Prevention:**
- Configure CORS before testing
- Use specific origins in production
- Test with browser developer tools

---

## Tool Execution Errors

### Issue 1: Query Syntax Error

**Symptoms:**
```
ArangoError: [HTTP 400][ERR 1501] AQL: syntax error, unexpected identifier near '...'
```

**Causes:**
- Invalid AQL syntax
- Missing bind variables
- Wrong collection name

**Solutions:**

**1. Test query in ArangoDB web UI:**
```
# http://localhost:8529
# Queries → New Query
# Test and debug query
```

**2. Use bind variables:**
```json
{
  "tool": "arango_query",
  "arguments": {
    "query": "FOR doc IN @@collection FILTER doc.age > @minAge RETURN doc",
    "bind_vars": {
      "@collection": "users",
      "minAge": 18
    }
  }
}
```

**3. Check AQL documentation:**
https://docs.arangodb.com/stable/aql/

**Prevention:**
- Always test queries in web UI first
- Use bind variables for dynamic values
- Use query builder tool: `arango_query_builder`

---

### Issue 2: Collection Not Found

**Symptoms:**
```
ArangoError: [HTTP 404][ERR 1203] collection or view not found: users
```

**Causes:**
- Collection doesn't exist
- Wrong collection name
- Wrong database

**Solutions:**

**1. List collections:**
```json
{
  "tool": "arango_list_collections",
  "arguments": {}
}
```

**2. Create collection:**
```json
{
  "tool": "arango_create_collection",
  "arguments": {
    "name": "users"
  }
}
```

**3. Verify database:**
```bash
# .env
ARANGO_DB=mcp_arangodb_test
```

**Prevention:**
- Create collections before querying
- Use `arango_list_collections` to verify
- Document required collections

---

### Issue 3: Permission Denied

**Symptoms:**
```
ArangoError: [HTTP 403][ERR 11] insufficient permissions
```

**Causes:**
- User lacks required permissions
- Read-only user trying to write
- Database-level restrictions

**Solutions:**

**1. Check user permissions:**
```
# Web UI: http://localhost:8529
# Users → Select user → Permissions
```

**2. Grant permissions:**
```powershell
# Re-run setup script with correct permissions
pwsh -File .\scripts\setup-arango.ps1
```

**3. Use admin user (development only):**
```bash
# .env
ARANGO_USERNAME=root
ARANGO_PASSWORD=changeme
```

**Prevention:**
- Grant appropriate permissions during setup
- Use dedicated user with minimal required permissions
- Document required permissions

---

## Performance Issues

### Issue 1: Slow Query Execution

**Symptoms:**
- Queries take >5 seconds
- Timeout errors
- High CPU usage

**Causes:**
- Missing indexes
- Full collection scans
- Complex joins
- Large result sets

**Solutions:**

**1. Profile query:**
```json
{
  "tool": "arango_query_profile",
  "arguments": {
    "query": "FOR doc IN users FILTER doc.email == 'test@example.com' RETURN doc"
  }
}
```

**2. Create indexes:**
```json
{
  "tool": "arango_create_index",
  "arguments": {
    "collection": "users",
    "fields": ["email"],
    "type": "persistent",
    "unique": true
  }
}
```

**3. Optimize query:**
```aql
# Add LIMIT
FOR doc IN users LIMIT 100 RETURN doc

# Use indexes
FOR doc IN users FILTER doc.email == @email RETURN doc

# Avoid full scans
FOR doc IN users FILTER doc.status IN ['active', 'pending'] RETURN doc
```

**Prevention:**
- Create indexes for frequently queried fields
- Use LIMIT for large collections
- Profile queries before production

---

### Issue 2: High Memory Usage

**Symptoms:**
- Docker container using >2GB RAM
- Out of memory errors
- System slowdown

**Causes:**
- Large result sets
- Memory leaks
- Too many concurrent connections

**Solutions:**

**1. Increase Docker memory:**
```
# Docker Desktop → Settings → Resources
# Increase Memory to 4GB+
```

**2. Use pagination:**
```aql
# Instead of returning all results
FOR doc IN large_collection LIMIT 1000 RETURN doc
```

**3. Monitor memory:**
```powershell
docker stats mcp_arangodb_test
```

**Prevention:**
- Use LIMIT in queries
- Implement pagination
- Monitor resource usage

---

## Docker Issues

### Issue 1: Container Won't Start

**Symptoms:**
```
Error: Container exited with code 1
Health check failed
```

**Causes:**
- Port conflict
- Insufficient resources
- Corrupted data volume

**Solutions:**

**1. Check logs:**
```powershell
docker compose logs arangodb
```

**2. Check port availability:**
```powershell
netstat -ano | findstr :8529
```

**3. Recreate container:**
```powershell
docker compose down
docker compose up -d arangodb
```

**4. Remove data volume (⚠️ deletes data):**
```powershell
docker compose down -v
docker compose up -d arangodb
```

**Prevention:**
- Use health checks
- Allocate sufficient resources
- Regular backups

---

### Issue 2: Health Check Failing

**Symptoms:**
```
Container status: unhealthy
Health check: failing
```

**Causes:**
- Wrong root password in health check
- ArangoDB not fully started
- Resource constraints

**Solutions:**

**1. Check health check command:**
```yaml
# docker-compose.yml
healthcheck:
  test: arangosh --server.username root --server.password "$ARANGO_ROOT_PASSWORD" ...
```

**2. Verify password matches:**
```bash
# .env
ARANGO_ROOT_PASSWORD=changeme
```

**3. Increase health check timeout:**
```yaml
healthcheck:
  interval: 10s
  timeout: 5s
  retries: 30
```

**Prevention:**
- Use consistent passwords
- Increase health check retries
- Monitor container logs

---

## Getting Help

### Before Asking for Help

1. **Check this troubleshooting guide**
2. **Review logs:**
   - Claude Desktop: `%APPDATA%\Claude\logs\`
   - Docker: `docker compose logs arangodb`
   - Server: `LOG_LEVEL=DEBUG`
3. **Test health check:**
   ```powershell
   python -m mcp_arangodb_async --health
   ```
4. **Verify configuration:**
   - Environment variables
   - Docker container status
   - Network connectivity

### Where to Get Help

- **GitHub Issues:** https://github.com/PCfVW/mcp-arango-async/issues
- **Discussions:** https://github.com/PCfVW/mcp-arango-async/discussions
- **Documentation:** https://github.com/PCfVW/mcp-arango-async/tree/main/docs

### Information to Include

When reporting issues, include:

1. **Environment:**
   - OS and version
   - Python version
   - Docker version
   - ArangoDB version

2. **Configuration:**
   - Environment variables (redact passwords)
   - MCP client configuration
   - Docker Compose configuration

3. **Logs:**
   - Error messages
   - Stack traces
   - Docker logs
   - Health check output

4. **Steps to Reproduce:**
   - What you did
   - What you expected
   - What actually happened

---

## Related Documentation

- [Installation Guide](../getting-started/installation.md)
- [Environment Variables](../configuration/environment-variables.md)
- [Transport Configuration](../configuration/transport-configuration.md)
- [Tools Reference](tools-reference.md)

