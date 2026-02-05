# Low-Level MCP Server Rationale

Why we chose `mcp.server.lowlevel.Server` instead of FastMCP for the mcp-arangodb-async project.

**Audience:** Developers and Contributors  
**Prerequisites:** Understanding of MCP protocol, Python async programming  
**Estimated Time:** 15-20 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [MCP Server Implementation Options](#mcp-server-implementation-options)
3. [Our Decision: Low-Level Server](#our-decision-low-level-server)
4. [When to Use Each Approach](#when-to-use-each-approach)
5. [Related Documentation](#related-documentation)

---

## Overview

The Model Context Protocol (MCP) Python SDK provides two approaches for implementing MCP servers:

1. **FastMCP** - High-level, decorator-based framework
2. **Low-Level Server** - Direct access to MCP protocol primitives

This document explains why we chose the low-level approach for mcp-arangodb-async.

---

## MCP Server Implementation Options

### FastMCP (High-Level Framework)

**What it is:** Simplified framework with automatic tool registration and lifecycle management

**Example:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
def my_tool(arg: str) -> str:
    """Tool description."""
    return f"Result: {arg}"

# FastMCP handles everything else
```

**Pros:**
- ✅ Minimal boilerplate
- ✅ Automatic tool registration
- ✅ Built-in HTTP transport
- ✅ Quick to get started

**Cons:**
- ❌ Limited lifecycle control
- ❌ No runtime state modification
- ❌ Opinionated structure
- ❌ Harder to customize

---

### Low-Level Server (Direct API)

**What it is:** Direct access to MCP protocol primitives with full control

**Example:**
```python
from mcp.server.lowlevel import Server

server = Server("my-server", lifespan=custom_lifespan)

@server.list_tools()
async def handle_list_tools():
    return [Tool(name="my_tool", ...)]

@server.call_tool()
async def call_tool(name, arguments):
    # Custom routing logic
    return execute_tool(name, arguments)
```

**Pros:**
- ✅ Full lifecycle control
- ✅ Runtime state modification
- ✅ Custom routing logic
- ✅ Maximum flexibility

**Cons:**
- ❌ More boilerplate
- ❌ Manual tool registration
- ❌ Requires HTTP transport implementation
- ❌ Steeper learning curve

---

## Our Decision: Low-Level Server

We chose the low-level Server API for **five critical reasons**:

### 1. Complex Startup Logic with Retry/Reconnect ⭐

**The Challenge:**  
ArangoDB may not be available when the server starts (Docker startup order, network issues, etc.).

**Our Solution:**
```python
@asynccontextmanager
async def server_lifespan(server: Server):
    """Initialize ArangoDB with retry logic."""
    cfg = load_config()
    client = None
    db = None
    
    # Configurable retry logic
    retries = int(os.getenv("ARANGO_CONNECT_RETRIES", "3"))
    delay = float(os.getenv("ARANGO_CONNECT_DELAY_SEC", "1.0"))
    
    for attempt in range(1, retries + 1):
        try:
            client, db = get_client_and_db(cfg)
            logger.info(f"Connected to ArangoDB (attempt {attempt})")
            break
        except Exception:
            logger.warning(f"Connection attempt {attempt} failed")
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                logger.error("Failed to connect; starting without DB")
                client = None
                db = None
    
    # Graceful degradation: start even if DB unavailable
    yield {"db": db, "client": client}
    
    # Cleanup
    if client:
        client.close()
```

**Why FastMCP Can't Do This:**  
FastMCP's lifespan API is simpler and doesn't provide the same level of control over initialization flow, retry logic, or graceful degradation.

---

### 2. Runtime State Modification ⭐

**The Challenge:**  
If database connection fails at startup, we want to retry during the first tool call (lazy connection recovery).

**Our Solution:**
```python
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    """Execute tool with lazy connection recovery."""
    ctx = server.request_context
    db = ctx.lifespan_context.get("db")
    
    # Lazy connection recovery
    if db is None:
        try:
            cfg = load_config()
            client, db_conn = get_client_and_db(cfg)
            
            # Dynamically update lifespan context
            ctx.lifespan_context["db"] = db_conn
            ctx.lifespan_context["client"] = client
            db = db_conn
            
            logger.info("Lazy connection recovery successful")
        except Exception as e:
            return _json_content({
                "error": "Database unavailable",
                "message": str(e),
                "hint": "Ensure ArangoDB is running"
            })
    
    # Now execute the tool
    tool_reg = TOOL_REGISTRY.get(name)
    result = tool_reg.handler(db, arguments)
    return _json_content(result)
```

**Why FastMCP Can't Do This:**  
FastMCP doesn't expose the request context or lifespan context for runtime modification.

---

### 3. Centralized Routing for 34+ Tools ⭐

**The Challenge:**  
We have 34 tools. Managing them with if-elif chains is error-prone and slow.

**Our Solution:**
```python
# Tool registry (O(1) lookup)
TOOL_REGISTRY: Dict[str, ToolRegistration] = {}

@register_tool(name=ARANGO_QUERY, description="...", model=QueryArgs)
@handle_errors
def handle_arango_query(db, args):
    """Execute AQL query."""
    return {"results": list(db.aql.execute(args["query"]))}

# Centralized dispatch
@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]):
    tool_reg = TOOL_REGISTRY.get(name)  # O(1) lookup
    if tool_reg is None:
        return _json_content({"error": f"Unknown tool: {name}"})
    
    # Validate with Pydantic
    validated_args = tool_reg.model(**arguments).model_dump()
    
    # Execute handler
    result = tool_reg.handler(db, validated_args)
    return _json_content(result)
```

**Benefits:**
- O(1) tool lookup (vs O(n) if-elif chain)
- Single point for validation, error handling, logging
- Easy to add/remove tools
- Consistent error formatting

**Why FastMCP Can't Do This:**  
FastMCP uses decorators for routing, which is fine for small servers but doesn't provide the same centralized control for large tool sets.

---

### 4. Extensive Test Suite Compatibility ⭐

**The Challenge:**
We have 230+ tests that directly access `server.request_context` and `server._handlers`.

**Our Solution:**
```python
# Test compatibility shims
def _safe_get_request_context(self):
    """Get request context with fallback for tests."""
    if hasattr(self, "_request_contexts"):
        ctx_var = self._request_contexts.get(asyncio.current_task())
        if ctx_var:
            return ctx_var.get()
    # Fallback for tests
    return type('RequestContext', (), {
        'lifespan_context': getattr(self, '_test_lifespan_context', {})
    })()

# Apply to Server class
setattr(Server, "request_context", property(_safe_get_request_context, ...))
```

**Why This Matters:**
Migrating to FastMCP would require rewriting 230+ tests. The low-level API preserves our existing test infrastructure.

---

### 5. Custom Error Handling Strategy ⭐

**The Challenge:**  
We need consistent error formatting across all tools with detailed context.

**Our Solution:**
```python
def handle_errors(func):
    """Decorator for consistent error handling."""
    def wrapper(db, args=None):
        try:
            return func(db, args) if args else func(db)
        except KeyError as e:
            return {
                "error": "ValidationError",
                "message": f"Missing required parameter: {e}",
                "tool": func.__name__
            }
        except ArangoError as e:
            return {
                "error": "DatabaseError",
                "message": str(e),
                "type": type(e).__name__,
                "tool": func.__name__
            }
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            return {
                "error": "InternalError",
                "message": str(e),
                "tool": func.__name__
            }
    return wrapper

# Apply to all handlers
@register_tool(name=ARANGO_QUERY, ...)
@handle_errors
def handle_arango_query(db, args):
    # Errors automatically caught and formatted
    pass
```

**Benefits:**
- Consistent error format across all tools
- Detailed error context (tool name, error type)
- Centralized logging
- Easy to extend (add metrics, tracing, etc.)

---

## When to Use Each Approach

### Use FastMCP When:

✅ Simple tool registration is sufficient  
✅ Database is always available at startup  
✅ No need for runtime context modification  
✅ Starting a new project from scratch  
✅ Fewer than 10 tools  
✅ No complex lifecycle requirements

**Example Use Case:** Simple API wrapper with 3-5 tools, database always available

---

### Use Low-Level Server When:

✅ Complex startup logic required  
✅ Need runtime state modification  
✅ Extensive existing test suite  
✅ Centralized routing logic preferred  
✅ Custom lifecycle management needed  
✅ Large number of tools (10+)  
✅ Advanced error handling requirements

**Example Use Case:** Database server with 30+ tools, retry logic, lazy connection recovery (like mcp-arangodb-async)

---

## What We Gain

By using the low-level Server API, we achieve:

1. **Full Control** - Complete flexibility over server lifecycle
2. **Advanced Features** - Retry logic, lazy reconnection, runtime state modification
3. **Test Compatibility** - Preserve 230+ existing tests
4. **Centralized Logic** - Single point for cross-cutting concerns
5. **Scalability** - O(1) tool dispatch for 34+ tools

---

## Conclusion

The low-level MCP Server API is the right choice for mcp-arangodb-async because:

- ✅ We need complex startup logic with retry/reconnect
- ✅ We need runtime state modification for lazy connection recovery
- ✅ We have 34+ tools requiring centralized routing
- ✅ We have 230+ tests that depend on low-level API
- ✅ We need custom error handling across all tools

FastMCP is excellent for simple servers, but our requirements demand the flexibility and control of the low-level API.

---

## Related Documentation

- [Architecture Overview](architecture.md)
- [HTTP Transport Implementation](http-transport.md)
- [Transport Configuration](../configuration/transport-configuration.md)
- [Tools Reference](../user-guide/tools-reference.md)

