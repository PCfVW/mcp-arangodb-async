# Design Decisions

Key architectural decisions and rationale for the mcp-arangodb-async server implementation.

**Audience:** Developers and Contributors  
**Prerequisites:** Understanding of MCP protocol basics  
**Estimated Time:** 20-30 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [Low-Level MCP Server API](#low-level-mcp-server-api)
3. [Docker Rationale](#docker-rationale)
4. [Retry and Reconnect Logic](#retry-and-reconnect-logic)
5. [Tool Registration Pattern](#tool-registration-pattern)
6. [Error Handling Strategy](#error-handling-strategy)
7. [Related Documentation](#related-documentation)

---

## Overview

This document explains the **why** behind key architectural decisions in the mcp-arangodb-async server. Each decision represents a deliberate trade-off optimized for:

- **Reliability:** Graceful handling of database unavailability
- **Maintainability:** Clear patterns for adding new tools
- **Flexibility:** Support for complex lifecycle management
- **Performance:** Efficient request routing and validation

### Decision Summary

| Decision | Alternative Considered | Rationale |
|----------|------------------------|-----------|
| **Low-Level MCP Server API** | FastMCP | Complex startup logic, runtime state modification, centralized routing |
| **Docker for ArangoDB** | Native installation | Isolation, reproducibility, zero-install experience |
| **Retry/Reconnect Logic** | Fail-fast on startup | Database may not be ready (Docker startup order) |
| **Decorator-Based Registration** | Manual if-elif chain | Single source of truth, O(1) dispatch, type safety |
| **Centralized Error Handling** | Per-tool error handling | Consistent error format, shared recovery logic |

---

## Low-Level MCP Server API

### The Decision

Use **`mcp.server.lowlevel.Server`** instead of **FastMCP** for server implementation.

### Context: Two MCP Server Approaches

**FastMCP (High-Level):**
```python
from mcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
async def arango_query(query: str, bind_vars: dict = None):
    # Each tool is independent
    # Simple, declarative, minimal boilerplate
    return execute_query(query, bind_vars)
```

**Low-Level Server (Our Choice):**
```python
from mcp.server.lowlevel import Server

server = Server("mcp-arangodb-async", lifespan=server_lifespan)

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    # Single interception point for all 34 tools
    # Full control over lifecycle, context, routing
    handler = TOOL_REGISTRY.get(name)
    return await handler(db, arguments)
```

### Why Low-Level Server?

#### 1. Complex Startup Logic with Retry/Reconnect ⭐

**The Challenge:**
ArangoDB may not be available when the server starts (Docker startup order, network issues, configuration errors).

**Our Approach:**
```python
@asynccontextmanager
async def server_lifespan(server: Server) -> AsyncIterator[Dict[str, Any]]:
    """Initialize ArangoDB client with retry logic."""
    client = None
    db = None
    max_retries = 5
    retry_delay = 2.0
    
    for attempt in range(max_retries):
        try:
            client = ArangoClient(hosts=url)
            db = client.db(db_name, username=username, password=password)
            # Verify connection
            db.version()
            logger.info(f"Connected to ArangoDB: {db_name}")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Connection attempt {attempt + 1} failed, retrying...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error("Failed to connect after all retries")
                # Continue with db=None (graceful degradation)
    
    try:
        yield {"db": db, "client": client}
    finally:
        if client:
            client.close()
```

**Why This Matters:**
- **Docker Compose:** ArangoDB container may take 10-15 seconds to become healthy
- **Network Issues:** Temporary connectivity problems shouldn't crash the server
- **Graceful Degradation:** Server can start even if database is unavailable (returns helpful errors)

**FastMCP Alternative:**
FastMCP doesn't provide built-in lifecycle management with retry logic. You'd need to implement this separately, losing the integration benefits.

---

#### 2. Runtime State Modification

**The Challenge:**
We need to modify server state at runtime (e.g., lazy connection recovery, context manipulation).

**Our Approach:**
```python
# Access request context during tool execution
ctx = server.request_context
db = ctx.lifespan_context.get("db") if ctx and ctx.lifespan_context else None

# Lazy connection recovery
if db is None:
    # Attempt reconnection
    db = await reconnect_to_database()
    # Update context for subsequent requests
    ctx.lifespan_context["db"] = db
```

**Why This Matters:**
- **Connection Recovery:** If database connection is lost, we can reconnect without restarting the server
- **Dynamic Configuration:** Can update connection parameters at runtime
- **Monitoring:** Can inject metrics collection, logging, or tracing

**FastMCP Alternative:**
FastMCP provides limited access to request context. Runtime state modification requires workarounds.

---

#### 3. Centralized Routing for 34+ Tools

**The Challenge:**
With 34 tools (and growing), we need efficient dispatch and shared logic.

**Our Approach:**
```python
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    # Single interception point for ALL tools
    # - Unified validation (Pydantic)
    # - Shared error handling
    # - Lazy connection recovery
    # - Metrics and monitoring
    # - O(1) dispatch via dictionary lookup
    
    tool_reg = TOOL_REGISTRY.get(name)
    if tool_reg is None:
        return _json_content({"error": f"Unknown tool: {name}"})
    
    # Validate arguments
    parsed = tool_reg.model(**(arguments or {}))
    validated_args = parsed.model_dump(exclude_none=True)
    
    # Execute handler
    result = await tool_reg.handler(db, validated_args)
    return _json_content(result)
```

**Benefits:**
- **O(1) Dispatch:** Dictionary lookup instead of O(n) if-elif chain
- **Shared Logic:** Validation, error handling, logging in one place
- **Easy Monitoring:** Add metrics collection for all tools at once
- **Consistent Errors:** All tools return errors in the same format

**FastMCP Alternative:**
```python
@mcp.tool()
async def arango_query(query: str, bind_vars: dict = None):
    # Each tool is independent
    # Shared logic must be duplicated or abstracted
    try:
        # Validation logic (repeated 34 times)
        # Error handling (repeated 34 times)
        # Logging (repeated 34 times)
        return execute_query(query, bind_vars)
    except Exception as e:
        # Error formatting (repeated 34 times)
        return {"error": str(e)}
```

---

#### 4. Extensive Test Suite Compatibility

**The Challenge:**
We have 100+ tests that rely on low-level Server API patterns.

**Our Approach:**
- Tests directly instantiate `Server` with custom lifespan
- Tests mock `request_context` for isolated testing
- Tests verify tool registration via `TOOL_REGISTRY`

**Migration Cost:**
Migrating to FastMCP would require rewriting the entire test suite, introducing risk and delaying feature development.

---

### Trade-Offs

**What We Gain:**
✅ Full control over lifecycle management  
✅ Runtime state modification  
✅ Centralized routing and error handling  
✅ Test suite compatibility  
✅ Flexibility for future enhancements

**What We Lose:**
❌ More boilerplate code  
❌ Steeper learning curve for contributors  
❌ Manual tool registration (mitigated by decorator pattern)

### When to Reconsider

Consider migrating to FastMCP if:
- FastMCP adds built-in retry/reconnect lifecycle management
- We simplify to <10 tools with no shared logic
- Test suite is rewritten for other reasons
- FastMCP provides equivalent context manipulation

---

## Docker Rationale

### The Decision

Run ArangoDB 3.11 in Docker with persistent volumes instead of native installation.

### Why Docker?

#### 1. Stability and Isolation

**Problem:** Native database installations can conflict with host system packages, ports, and configurations.

**Solution:**
```yaml
services:
  arangodb:
    image: arangodb:3.11
    container_name: mcp_arangodb_test
    ports:
      - "8529:8529"
    volumes:
      - arango_data:/var/lib/arangodb3
```

**Benefits:**
- **No Host Conflicts:** Database runs in isolated container
- **Port Management:** Easy to change port mapping without reconfiguring database
- **Clean Uninstall:** Remove container and volume, no system-wide changes

---

#### 2. Zero-Install Database Experience

**User Experience:**
```powershell
# Start database
docker compose up -d

# Stop database
docker compose down

# Reset database (clean slate)
docker compose down -v
docker compose up -d
```

**Benefits:**
- **No Installation:** No need to download, install, configure ArangoDB
- **Cross-Platform:** Same commands on Windows, macOS, Linux
- **Fast Reset:** Recreate clean instances in seconds

---

## Tool Registration Pattern

### The Decision

Use decorator-based tool registration with centralized `TOOL_REGISTRY` instead of manual if-elif chains.

### Evolution of Tool Registration

#### Phase 1: Manual if-elif Chain (Original)

**Problem:** Adding new tools required changes in 3 places:

```python
# 1. Define Pydantic model
class ArangoQueryArgs(BaseModel):
    query: str
    bind_vars: Optional[Dict[str, Any]] = None

# 2. Add to model map
TOOL_MODELS = {
    "arango_query": ArangoQueryArgs,
    # ... 33 more entries
}

# 3. Add to if-elif chain
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    if name == "arango_query":
        return await handle_arango_query(db, arguments)
    elif name == "arango_list_collections":
        return await handle_arango_list_collections(db, arguments)
    # ... 33 more elif branches
    else:
        return {"error": "Unknown tool"}

# 4. Add to manual tool list
@server.list_tools()
async def handle_list_tools():
    return [
        types.Tool(name="arango_query", description="...", inputSchema=...),
        # ... 33 more entries
    ]
```

**Issues:**
- **Error-Prone:** Easy to forget updating one of the 4 locations
- **O(n) Dispatch:** if-elif chain requires checking each tool sequentially
- **Maintenance Burden:** Adding tool #35 requires scrolling through 34 existing tools
- **No Type Safety:** Easy to mismatch tool name strings

---

#### Phase 2: Decorator-Based Registration (Current)

**Solution:** Single source of truth with `@register_tool()` decorator:

```python
from mcp_arangodb_async.tool_registry import register_tool
from mcp_arangodb_async.tools import ARANGO_QUERY

@register_tool(
    name=ARANGO_QUERY,
    description="Execute AQL query with optional bind variables",
    model=ArangoQueryArgs,
)
async def handle_arango_query(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute AQL query and return results."""
    query = args["query"]
    bind_vars = args.get("bind_vars")

    cursor = db.aql.execute(query, bind_vars=bind_vars)
    return list(cursor)
```

**What Happens:**
1. **Decorator Execution:** When `handlers.py` is imported, all `@register_tool()` decorators execute
2. **Registry Population:** Each decorator adds entry to `TOOL_REGISTRY` dictionary
3. **Automatic Tool List:** `handle_list_tools()` generates tool list from registry
4. **O(1) Dispatch:** `call_tool()` uses dictionary lookup

---

### Tool Registry Structure

**ToolRegistration Dataclass:**
```python
@dataclass(frozen=True)
class ToolRegistration:
    """Metadata for a registered tool."""
    name: str
    description: str
    model: Type[BaseModel]
    handler: Callable[[StandardDatabase, Dict[str, Any]], Awaitable[Dict[str, Any]]]
```

**Global Registry:**
```python
TOOL_REGISTRY: Dict[str, ToolRegistration] = {}
```

**Registration Decorator:**
```python
def register_tool(name: str, description: str, model: Type[BaseModel]) -> Callable:
    """Register a tool handler with duplicate detection."""
    def decorator(handler: Callable) -> Callable:
        if name in TOOL_REGISTRY:
            raise ValueError(f"Tool '{name}' is already registered")

        TOOL_REGISTRY[name] = ToolRegistration(
            name=name,
            description=description,
            model=model,
            handler=handler,
        )
        return handler
    return decorator
```

---

### Benefits

#### 1. Single Source of Truth

**Before (4 locations):**
- Pydantic model definition
- TOOL_MODELS dictionary
- if-elif chain
- Manual tool list

**After (1 location):**
- `@register_tool()` decorator with all metadata

---

#### 2. O(1) Dispatch

**Before (O(n)):**
```python
if name == "arango_query":
    # ...
elif name == "arango_list_collections":
    # ...
# ... 32 more elif branches
```

**After (O(1)):**
```python
tool_reg = TOOL_REGISTRY.get(name)
if tool_reg is None:
    return {"error": f"Unknown tool: {name}"}
```

---

#### 3. Duplicate Detection

**Decorator Validation:**
```python
if name in TOOL_REGISTRY:
    raise ValueError(f"Tool '{name}' is already registered")
```

**Prevents:**
- Accidental tool name collisions
- Overwriting existing tools
- Silent failures from typos

---

#### 4. Type Safety

**Tool Name Constants:**
```python
# tools.py
ARANGO_QUERY = "arango_query"
ARANGO_LIST_COLLECTIONS = "arango_list_collections"
# ... 32 more constants

# handlers.py
@register_tool(
    name=ARANGO_QUERY,  # Type-safe constant, not string literal
    description="...",
    model=ArangoQueryArgs,
)
```

**Benefits:**
- IDE autocomplete for tool names
- Refactoring support (rename symbol)
- Compile-time error detection

---

### Trade-Offs

**What We Gain:**
✅ Single source of truth (1 location instead of 4)
✅ O(1) dispatch (dictionary lookup)
✅ Duplicate detection (prevents collisions)
✅ Type safety (constants instead of strings)
✅ Easy to add new tools (just add decorator)

**What We Lose:**
❌ Decorator magic (less explicit than manual registration)
❌ Import-time side effects (decorators execute on import)

---

## Error Handling Strategy

### The Decision

Implement centralized error handling with consistent error format across all tools.

### Error Handling Architecture

#### 1. Centralized Error Wrapper

**Decorator Pattern:**
```python
def handle_errors(func: Callable) -> Callable:
    """Wrap handler with consistent error handling."""
    @wraps(func)
    async def wrapper(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await func(db, args)
        except ArangoServerError as e:
            return {
                "error": "ArangoServerError",
                "message": str(e),
                "code": e.error_code,
                "http_code": e.http_code,
            }
        except ValidationError as e:
            return {
                "error": "ValidationError",
                "details": json.loads(e.json()),
            }
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            return {
                "error": "InternalError",
                "message": str(e),
            }
    return wrapper
```

**Usage:**
```python
@register_tool(name=ARANGO_QUERY, description="...", model=ArangoQueryArgs)
@handle_errors
async def handle_arango_query(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    # Tool implementation
    # Errors are automatically caught and formatted
    pass
```

---

#### 2. Consistent Error Format

**All Errors Follow This Structure:**
```json
{
  "error": "ErrorType",
  "message": "Human-readable description",
  "details": {},  // Optional: Additional context
  "tool": "tool_name"  // Added by call_tool()
}
```

**Error Types:**
- `DatabaseUnavailable` - Database connection not established
- `ArangoServerError` - ArangoDB-specific errors (query syntax, constraints, etc.)
- `ValidationError` - Pydantic validation failures (invalid arguments)
- `InternalError` - Unexpected errors (bugs, system issues)

---

#### 3. Validation at Entry Point

**Two-Stage Validation:**

**Stage 1: Pydantic Validation (call_tool)**
```python
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    try:
        parsed = tool_reg.model(**(arguments or {}))
        validated_args = parsed.model_dump(exclude_none=True)
    except ValidationError as ve:
        return _json_content({
            "error": "ValidationError",
            "tool": name,
            "details": json.loads(ve.json()),
        })
```

**Stage 2: Handler Execution (with error wrapper)**
```python
result = await tool_reg.handler(db, validated_args)
```

**Benefits:**
- **Early Validation:** Invalid arguments rejected before handler execution
- **Type Safety:** Handlers receive validated, typed arguments
- **Clear Errors:** Pydantic provides detailed validation error messages

---

#### 4. Graceful Degradation

**Database Unavailable:**
```python
db = ctx.lifespan_context.get("db") if ctx and ctx.lifespan_context else None

if db is None:
    return _json_content({
        "error": "DatabaseUnavailable",
        "message": "ArangoDB connection not established. Check server logs and database configuration.",
        "tool": name
    })
```

**User Experience:**
- Server doesn't crash
- Clear error message explains the issue
- User can fix configuration and retry

---

### Error Handling Examples

#### Example 1: Validation Error

**Request:**
```json
{
  "tool": "arango_query",
  "arguments": {
    "query": 123  // Invalid: should be string
  }
}
```

**Response:**
```json
{
  "error": "ValidationError",
  "tool": "arango_query",
  "details": [
    {
      "loc": ["query"],
      "msg": "Input should be a valid string",
      "type": "string_type"
    }
  ]
}
```

---

#### Example 2: ArangoDB Error

**Request:**
```json
{
  "tool": "arango_query",
  "arguments": {
    "query": "FOR doc IN nonexistent_collection RETURN doc"
  }
}
```

**Response:**
```json
{
  "error": "ArangoServerError",
  "message": "collection or view not found: nonexistent_collection",
  "code": 1203,
  "http_code": 404
}
```

---

#### Example 3: Database Unavailable

**Request:**
```json
{
  "tool": "arango_list_collections",
  "arguments": {}
}
```

**Response:**
```json
{
  "error": "DatabaseUnavailable",
  "message": "ArangoDB connection not established. Check server logs and database configuration.",
  "tool": "arango_list_collections"
}
```

---

### Trade-Offs

**What We Gain:**
✅ Consistent error format across all tools
✅ Centralized error handling (no duplication)
✅ Detailed error messages for debugging
✅ Graceful degradation (server doesn't crash)
✅ Type-safe validation with Pydantic

**What We Lose:**
❌ Slightly more complex decorator stack
❌ Generic error handling (less tool-specific customization)

---

## Related Documentation
- [Transport Comparison](transport-comparison.md)
- [Transport Configuration](../configuration/transport-configuration.md)
- [Low-Level MCP Rationale](../developer-guide/low-level-mcp-rationale.md)
- [Architecture Overview](../developer-guide/architecture.md)
#### 3. Reproducibility

**Problem:** "Works on my machine" issues due to different ArangoDB versions, configurations, or system environments.

**Solution:**
- **Fixed Version:** `arangodb:3.11` ensures everyone uses the same version
- **Declarative Config:** `docker-compose.yml` defines exact configuration
- **CI/CD Ready:** Same Docker setup works in GitHub Actions, GitLab CI, etc.

---

#### 4. Health Checks Built-In

**Configuration:**
```yaml
healthcheck:
  test: arangosh --server.username root --server.password "$ARANGO_ROOT_PASSWORD" --javascript.execute-string "require('@arangodb').db._version()" > /dev/null 2>&1 || exit 1
  interval: 5s
  timeout: 2s
  retries: 30
```

**Benefits:**
- **Readiness Validation:** Know when database is ready to accept connections
- **Automated Retry:** Server lifespan can wait for healthy status
- **Monitoring:** Docker reports health status (`docker compose ps`)

---

#### 5. Persistent Data Configuration

**Default Behavior (Ephemeral):**
Data is lost when container is removed.

**Recommended Configuration (Persistent):**
```yaml
volumes:
  - arango_data:/var/lib/arangodb3

volumes:
  arango_data:
```

**Benefits:**
- **Data Preservation:** Data survives container restarts and recreations
- **Backup-Friendly:** Volume can be backed up independently
- **Development Workflow:** Keep test data across development sessions

---

### Trade-Offs

**What We Gain:**
✅ Isolation and stability  
✅ Zero-install experience  
✅ Reproducibility across environments  
✅ Built-in health checks  
✅ Easy reset and cleanup

**What We Lose:**
❌ Requires Docker Desktop installation  
❌ Slight performance overhead (minimal for development)  
❌ Additional layer of abstraction

### When to Use Native Installation

Consider native installation if:
- Docker is not available (restricted environments)
- Maximum performance is critical (production with dedicated hardware)
- You need to test against multiple ArangoDB versions simultaneously

---

## Retry and Reconnect Logic

### The Decision

Implement retry logic in server lifespan with graceful degradation instead of fail-fast on startup.

### Why Retry Logic?

#### Problem: Database Unavailability at Startup

**Common Scenarios:**
1. **Docker Compose Startup Order:** MCP server starts before ArangoDB is healthy
2. **Network Issues:** Temporary connectivity problems
3. **Configuration Errors:** Wrong credentials, database name, etc.

**Fail-Fast Approach (Rejected):**
```python
async def server_lifespan(server: Server):
    client = ArangoClient(hosts=url)
    db = client.db(db_name, username=username, password=password)
    db.version()  # Fails immediately if database unavailable
    yield {"db": db}
```

**Problem:** Server crashes if database isn't ready, requiring manual restart.

---

#### Our Approach: Retry with Graceful Degradation

**Implementation:**
```python
max_retries = 5
retry_delay = 2.0

for attempt in range(max_retries):
    try:
        client = ArangoClient(hosts=url)
        db = client.db(db_name, username=username, password=password)
        db.version()
        logger.info(f"Connected to ArangoDB: {db_name}")
        break
    except Exception as e:
        if attempt < max_retries - 1:
            logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
            await asyncio.sleep(retry_delay)
        else:
            logger.error("Failed to connect after all retries")
            # Continue with db=None (graceful degradation)
```

**Benefits:**
- **Automatic Recovery:** Handles Docker startup delays (10-15 seconds typical)
- **User-Friendly:** Server starts successfully, returns helpful errors if database unavailable
- **Debugging:** Logs show connection attempts, making issues easier to diagnose

---

#### Graceful Degradation

**Tool Execution with Unavailable Database:**
```python
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    db = ctx.lifespan_context.get("db") if ctx and ctx.lifespan_context else None
    
    if db is None:
        return _json_content({
            "error": "DatabaseUnavailable",
            "message": "ArangoDB connection not established. Check server logs and database configuration.",
            "tool": name
        })
    
    # Execute tool normally
    result = await tool_reg.handler(db, arguments)
    return _json_content(result)
```

**User Experience:**
- Server starts successfully (no crash)
- Tools return clear error messages explaining the issue
- User can fix configuration and retry without restarting server

---

### Configuration

**Environment Variables:**
```dotenv
ARANGO_URL=http://localhost:8529
ARANGO_DB=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password
ARANGO_TIMEOUT_SEC=30.0
```

**Retry Parameters (Hardcoded):**
- `max_retries`: 5 attempts
- `retry_delay`: 2.0 seconds between attempts
- **Total wait time:** Up to 10 seconds

---

### Trade-Offs

**What We Gain:**
✅ Handles Docker startup delays automatically  
✅ User-friendly error messages  
✅ Server doesn't crash on database unavailability  
✅ Easy debugging with detailed logs

**What We Lose:**
❌ Slightly longer startup time (up to 10 seconds)  
❌ More complex lifecycle management code

---


