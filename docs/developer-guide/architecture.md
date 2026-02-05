# Architecture Overview

System architecture and design patterns for mcp-arangodb-async.

**Audience:** Developers and Contributors  
**Prerequisites:** Understanding of MCP protocol, Python async programming, ArangoDB  
**Estimated Time:** 20-25 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [High-Level Architecture](#high-level-architecture)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Design Patterns](#design-patterns)
6. [Technology Stack](#technology-stack)
7. [Related Documentation](#related-documentation)

---

## Overview

The mcp-arangodb-async server is a production-ready MCP server that exposes ArangoDB operations to AI assistants. The architecture emphasizes:

✅ **Reliability** - Retry logic, graceful degradation, comprehensive error handling  
✅ **Flexibility** - Dual transport (stdio/HTTP), runtime state modification  
✅ **Scalability** - O(1) tool dispatch, stateless HTTP mode  
✅ **Maintainability** - Centralized routing, decorator-based registration  
✅ **Type Safety** - Pydantic validation for all inputs

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MCP Client Layer                         │
│  (Claude Desktop, Augment Code, Web Apps, Custom Clients)       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ MCP Protocol (JSON-RPC 2.0)
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                      Transport Layer                             │
│  ┌──────────────────┐              ┌─────────────────────────┐  │
│  │  stdio Transport │              │   HTTP Transport        │  │
│  │  (stdin/stdout)  │              │   (Starlette/uvicorn)   │  │
│  └──────────────────┘              └─────────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ MCP Server API
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                      MCP Server Core                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Server Lifespan (Async Context Manager)                 │   │
│  │  • Database connection with retry logic                  │   │
│  │  • Graceful degradation (start without DB)               │   │
│  │  • Lazy connection recovery                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Request Handlers                                         │   │
│  │  • list_tools() - Generate tool list from registry       │   │
│  │  • call_tool() - Centralized tool dispatch               │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ Tool Registry (O(1) lookup)
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                      Tool Layer                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Tool Registry (TOOL_REGISTRY)                            │   │
│  │  • 34 registered tools                                    │   │
│  │  • Metadata: name, description, Pydantic model            │   │
│  │  • Handler function reference                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Tool Handlers (handlers.py)                              │   │
│  │  • @register_tool() decorator                             │   │
│  │  • @handle_errors decorator                               │   │
│  │  • Pydantic validation                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ python-arango API
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                   Database Layer                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Connection Manager (db.py)                               │   │
│  │  • Singleton pattern                                      │   │
│  │  • Connection pooling                                     │   │
│  │  • Retry logic                                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  ArangoDB Client (python-arango)                          │   │
│  │  • HTTP connection pool                                   │   │
│  │  • Request/response handling                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ HTTP/HTTPS
                     │
┌────────────────────┴────────────────────────────────────────────┐
│                   ArangoDB Server                                │
│  (Docker Container: arangodb:3.11)                               │
│  • Multi-model database (documents, graphs, key-value)           │
│  • AQL query engine                                              │
│  • Graph traversal engine                                        │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Entry Point (`entry.py`)

**Responsibilities:**
- Server initialization
- Lifespan management
- Request routing
- Transport selection

**Key Components:**
```python
# Server instance
server = Server("mcp-arangodb-async", lifespan=server_lifespan)

# Lifespan context manager
@asynccontextmanager
async def server_lifespan(server: Server):
    # Initialize database with retry logic
    # Yield context with db and client
    # Cleanup on shutdown

# Request handlers
@server.list_tools()
async def handle_list_tools():
    # Generate tool list from TOOL_REGISTRY

@server.call_tool()
async def call_tool(name, arguments):
    # Validate arguments with Pydantic
    # Dispatch to handler via registry
    # Return formatted response
```

---

### 2. Tool Registry (`tool_registry.py`)

**Responsibilities:**
- Tool metadata storage
- Decorator-based registration
- Duplicate detection

**Key Components:**
```python
@dataclass
class ToolRegistration:
    name: str
    description: str
    model: Type[BaseModel]  # Pydantic model
    handler: Callable       # Handler function

# Global registry (O(1) lookup)
TOOL_REGISTRY: Dict[str, ToolRegistration] = {}

# Registration decorator
def register_tool(name: str, description: str, model: Type[BaseModel]):
    def decorator(handler: Callable):
        # Check for duplicates
        # Register in TOOL_REGISTRY
        return handler
    return decorator
```

**Benefits:**
- Single source of truth for tool metadata
- O(1) tool lookup
- Automatic duplicate detection
- Type-safe tool definitions

---

### 3. Tool Handlers (`handlers.py`)

**Responsibilities:**
- Tool implementation
- Error handling
- Database operations

**Key Components:**
```python
@register_tool(
    name=ARANGO_QUERY,
    description="Execute an AQL query",
    model=QueryArgs
)
@handle_errors
def handle_arango_query(db: StandardDatabase, args: Dict[str, Any]):
    """Execute AQL query with bind variables."""
    query = args["query"]
    bind_vars = args.get("bind_vars")
    cursor = db.aql.execute(query, bind_vars=bind_vars)
    return {"results": list(cursor)}
```

**Error Handling Decorator:**
```python
def handle_errors(func):
    """Centralized error handling for all tools."""
    def wrapper(db, args=None):
        try:
            return func(db, args) if args else func(db)
        except KeyError as e:
            return {"error": "ValidationError", "message": str(e)}
        except ArangoError as e:
            return {"error": "DatabaseError", "message": str(e)}
        except Exception as e:
            logger.exception(f"Unexpected error in {func.__name__}")
            return {"error": "InternalError", "message": str(e)}
    return wrapper
```

---

### 4. Pydantic Models (`models.py`)

**Responsibilities:**
- Input validation
- Type coercion
- JSON schema generation

**Example:**
```python
class QueryArgs(BaseModel):
    """Arguments for arango_query tool."""
    query: str = Field(..., description="AQL query string")
    bind_vars: Optional[Dict[str, Any]] = Field(
        None,
        description="Bind variables for query"
    )
```

**Benefits:**
- Automatic validation
- Clear error messages
- Type safety
- JSON schema for MCP clients

---

### 5. Database Connection (`db.py`)

**Responsibilities:**
- Connection management
- Retry logic
- Connection pooling

**Key Components:**
```python
class ConnectionManager:
    """Singleton connection manager."""
    _instance = None
    _lock = threading.Lock()
    
    def get_connection(self, cfg: Config):
        with self._lock:
            if self._client is None or not self._config_matches(cfg):
                # Create new connection
                self._client = ArangoClient(hosts=cfg.arango_url)
                self._db = self._client.db(cfg.database, ...)
            return self._client, self._db

async def connect_with_retry(cfg, retries=3, delay_sec=1.0):
    """Connect with exponential backoff."""
    for attempt in range(1, retries + 1):
        try:
            return get_client_and_db(cfg)
        except Exception:
            if attempt < retries:
                await asyncio.sleep(delay_sec)
    return None, None
```

---

### 6. Transport Layer

#### stdio Transport (`entry.py`)

**Responsibilities:**
- stdin/stdout communication
- JSON-RPC message handling
- Desktop client support

**Implementation:**
```python
async def run_stdio():
    """Run server with stdio transport."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-arangodb-async",
                server_version="0.2.7",
                capabilities=server.get_capabilities(...)
            )
        )
```

---

#### HTTP Transport (`http_transport.py`)

**Responsibilities:**
- HTTP request handling
- CORS configuration
- Session management
- Health checks

**Implementation:**
```python
def create_http_app(mcp_server, cors_origins, stateless):
    """Create Starlette app with MCP transport."""
    # Create session manager
    session_manager = StreamableHTTPSessionManager(
        mcp_server,
        stateless=stateless
    )
    
    # Create routes
    routes = [create_health_route(mcp_server)]
    app = Starlette(routes=routes)
    
    # Mount MCP endpoint
    app.mount("/mcp", session_manager.handle_request)
    
    # Add CORS middleware
    app = CORSMiddleware(
        app,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        expose_headers=["Mcp-Session-Id"]
    )
    
    return app, session_manager
```

---

## Data Flow

### Tool Execution Flow

```
1. MCP Client sends tool call request
   ↓
2. Transport layer receives JSON-RPC message
   ↓
3. Server.call_tool() handler invoked
   ↓
4. Lookup tool in TOOL_REGISTRY (O(1))
   ↓
5. Validate arguments with Pydantic model
   ↓
6. Check database availability
   ├─ If unavailable: Attempt lazy connection recovery
   └─ If available: Continue
   ↓
7. Execute tool handler with validated arguments
   ↓
8. Handler performs database operation
   ↓
9. @handle_errors decorator catches exceptions
   ↓
10. Format response as JSON
   ↓
11. Transport layer sends response to client
```

---

### Startup Flow

```
1. main() entry point
   ↓
2. Parse command-line arguments
   ↓
3. Determine transport type (stdio or HTTP)
   ↓
4. Initialize server with lifespan context manager
   ↓
5. server_lifespan() begins
   ├─ Load configuration from environment
   ├─ Attempt database connection (with retries)
   ├─ If successful: Store db in lifespan context
   └─ If failed: Store None (graceful degradation)
   ↓
6. Import handlers module (triggers @register_tool decorators)
   ↓
7. Tools registered in TOOL_REGISTRY
   ↓
8. Start transport (stdio or HTTP)
   ↓
9. Server ready to accept requests
```

---

### Error Handling Flow

```
1. Tool handler executes
   ↓
2. Exception occurs
   ↓
3. @handle_errors decorator catches exception
   ↓
4. Determine error type:
   ├─ KeyError → ValidationError
   ├─ ArangoError → DatabaseError
   └─ Exception → InternalError
   ↓
5. Format error response:
   {
     "error": "ErrorType",
     "message": "Error description",
     "tool": "tool_name"
   }
   ↓
6. Log error (with stack trace for InternalError)
   ↓
7. Return error response to client
```

---

## Design Patterns

### 1. Decorator Pattern

**Used for:**
- Tool registration (`@register_tool`)
- Error handling (`@handle_errors`)

**Benefits:**
- Separation of concerns
- Reusable cross-cutting logic
- Clean handler code

---

### 2. Registry Pattern

**Used for:**
- Tool metadata storage (`TOOL_REGISTRY`)

**Benefits:**
- O(1) tool lookup
- Single source of truth
- Easy to extend

---

### 3. Singleton Pattern

**Used for:**
- Database connection manager

**Benefits:**
- Connection reuse
- Thread-safe access
- Resource efficiency

---

### 4. Strategy Pattern

**Used for:**
- Transport selection (stdio vs HTTP)

**Benefits:**
- Runtime transport selection
- Easy to add new transports
- Clean separation

---

### 5. Context Manager Pattern

**Used for:**
- Server lifespan management
- Resource cleanup

**Benefits:**
- Guaranteed cleanup
- Exception safety
- Clear resource lifecycle

---

## Technology Stack

### Core Dependencies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **MCP SDK** | `mcp` | 1.18.0+ | Model Context Protocol implementation |
| **Database Driver** | `python-arango` | 8.2.2+ | ArangoDB client library |
| **Validation** | `pydantic` | 2.x | Input validation and type safety |
| **HTTP Framework** | `starlette` | 0.27.0+ | ASGI web framework for HTTP transport |
| **ASGI Server** | `uvicorn` | 0.23.0+ | Production ASGI server |
| **Environment** | `python-dotenv` | 1.0+ | Environment variable loading |

### Development Dependencies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Testing** | `pytest` | 8.x | Test framework |
| **Formatting** | `black` | 25.x | Code formatter |
| **Linting** | `ruff` | 0.1.0+ | Fast Python linter |

### Infrastructure

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Database** | ArangoDB | 3.11 | Multi-model database |
| **Container** | Docker | 20.x+ | Container runtime |
| **Orchestration** | Docker Compose | 2.x+ | Multi-container orchestration |

---

## Related Documentation

- [Low-Level MCP Rationale](low-level-mcp-rationale.md)
- [HTTP Transport Implementation](http-transport.md)
- [Tools Reference](../user-guide/tools-reference.md)
- [Environment Variables](../configuration/environment-variables.md)

