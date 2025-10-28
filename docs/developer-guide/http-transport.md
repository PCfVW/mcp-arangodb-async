# HTTP Transport Implementation

Complete guide to the HTTP transport implementation for mcp-arangodb-async.

**Audience:** Developers and DevOps Engineers  
**Prerequisites:** Understanding of HTTP, ASGI, Docker, and MCP protocol  
**Estimated Time:** 25-30 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Implementation Details](#implementation-details)
4. [Stateful vs Stateless Modes](#stateful-vs-stateless-modes)
5. [CORS Configuration](#cors-configuration)
6. [Deployment](#deployment)
7. [Security Considerations](#security-considerations)
8. [Migration from stdio](#migration-from-stdio)
9. [Related Documentation](#related-documentation)

---

## Overview

The HTTP transport enables mcp-arangodb-async to serve MCP requests over HTTP, supporting:

✅ **Web Applications** - Browser-based AI clients  
✅ **Containerized Deployments** - Docker, Kubernetes  
✅ **Horizontal Scaling** - Multiple server instances with load balancing  
✅ **Remote Access** - Network-accessible MCP server  
✅ **Health Checks** - Kubernetes readiness/liveness probes

### When to Use HTTP Transport

| Use Case | stdio | HTTP |
|----------|-------|------|
| **Desktop AI Clients** (Claude Desktop, Augment Code) | ✅ Recommended | ❌ Not supported |
| **Web Applications** | ❌ Not possible | ✅ Required |
| **Docker Compose** | ⚠️ Complex | ✅ Recommended |
| **Kubernetes** | ❌ Not practical | ✅ Required |
| **Horizontal Scaling** | ❌ Not possible | ✅ Supported |
| **Remote Access** | ❌ Not possible | ✅ Supported |

---

## Architecture

### Component Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    HTTP Client Layer                         │
│  (Browser, fetch API, axios, Python requests, etc.)         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP/HTTPS (JSON-RPC 2.0)
                     │
┌────────────────────┴────────────────────────────────────────┐
│                  Reverse Proxy (Optional)                    │
│  (nginx, Traefik, Caddy)                                     │
│  • TLS termination                                           │
│  • Load balancing                                            │
│  • Rate limiting                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                  CORS Middleware                             │
│  (Starlette CORSMiddleware)                                  │
│  • Origin validation                                         │
│  • Header exposure (Mcp-Session-Id)                          │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                  Starlette Application                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Routes                                               │   │
│  │  • /health - Health check endpoint                    │   │
│  │  • /mcp - MCP StreamableHTTP endpoint                 │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│           StreamableHTTPSessionManager                       │
│  (MCP SDK)                                                   │
│  • Session management (stateful/stateless)                   │
│  • JSON-RPC message handling                                 │
│  • Request/response streaming                                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────────┐
│                  MCP Server Core                             │
│  (Low-Level Server API)                                      │
│  • Tool dispatch                                             │
│  • Database operations                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## Implementation Details

### 1. Starlette Application Factory

**File:** `mcp_arangodb_async/http_transport.py`

```python
def create_http_app(
    mcp_server: Server,
    cors_origins: list[str] | None = None,
    stateless: bool = False,
) -> tuple[Starlette, StreamableHTTPSessionManager]:
    """Create Starlette app with MCP transport."""
    
    # 1. Create StreamableHTTP session manager
    session_manager = StreamableHTTPSessionManager(
        mcp_server,
        stateless=stateless,
    )
    
    # 2. Create routes
    routes = [
        create_health_route(mcp_server),
    ]
    
    # 3. Create Starlette app
    app = Starlette(routes=routes)
    
    # 4. Mount MCP endpoint
    app.mount("/mcp", session_manager.handle_request)
    
    # 5. Add CORS middleware
    app = CORSMiddleware(
        app,
        allow_origins=cors_origins or ["*"],
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],  # Critical!
    )
    
    return app, session_manager
```

**Key Points:**
- **StreamableHTTPSessionManager:** MCP SDK component for HTTP transport
- **CORS Middleware:** Must expose `Mcp-Session-Id` header for browser clients
- **Health Route:** Kubernetes readiness/liveness probe endpoint
- **Mount Point:** `/mcp` is the MCP protocol endpoint

---

### 2. StreamableHTTPSessionManager

**Purpose:** Manages MCP sessions over HTTP

**Modes:**
- **Stateful (default):** Maintains session state in memory
- **Stateless:** No session state, suitable for horizontal scaling

**Session Management:**
```python
# Stateful mode
session_manager = StreamableHTTPSessionManager(
    mcp_server,
    stateless=False,  # Default
)
# Sessions stored in memory
# Requires session affinity (sticky sessions) for load balancing

# Stateless mode
session_manager = StreamableHTTPSessionManager(
    mcp_server,
    stateless=True,
)
# No session state stored
# Can scale horizontally without session affinity
```

---

### 3. Health Check Endpoint

**Purpose:** Kubernetes readiness/liveness probes, monitoring

**Implementation:**
```python
def create_health_route(mcp_server: Server) -> Route:
    """Create health check route."""
    async def health_endpoint(request: Request) -> JSONResponse:
        # Access database from server's lifespan context
        ctx = mcp_server.request_context
        db = ctx.lifespan_context.get("db") if ctx else None
        
        # Get health status
        status = await health_check(db)
        
        # Return appropriate HTTP status code
        http_status = 200 if status["status"] == "healthy" else 503
        
        return JSONResponse(status, status_code=http_status)
    
    return Route("/health", health_endpoint, methods=["GET"])
```

**Response Format:**
```json
{
  "status": "healthy",
  "database": "connected",
  "server_version": "0.2.7",
  "timestamp": "2025-10-20T12:34:56Z"
}
```

**HTTP Status Codes:**
- **200 OK:** Server and database healthy
- **503 Service Unavailable:** Database unavailable or server unhealthy

---

### 4. uvicorn Server

**Purpose:** Production ASGI server

**Implementation:**
```python
async def run_http_server(
    mcp_server: Server,
    host: str = "0.0.0.0",
    port: int = 8000,
    stateless: bool = False,
    cors_origins: list[str] | None = None,
) -> None:
    """Run MCP server with HTTP transport."""
    
    # Create Starlette app
    app, session_manager = create_http_app(
        mcp_server,
        cors_origins=cors_origins,
        stateless=stateless,
    )
    
    # Create uvicorn config
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )
    
    # Create uvicorn server
    server = uvicorn.Server(config)
    
    # Run session manager and uvicorn concurrently
    async with session_manager.run():
        await server.serve()
```

**Configuration Options:**
- **host:** Bind address (`0.0.0.0` for all interfaces, `127.0.0.1` for localhost)
- **port:** Port number (default: 8000)
- **log_level:** Logging verbosity (`debug`, `info`, `warning`, `error`)
- **access_log:** Enable HTTP access logging

---

## Stateful vs Stateless Modes

### Stateful Mode (Default)

**Characteristics:**
- ✅ Session state maintained in memory
- ✅ Better performance (no session recreation)
- ✅ Suitable for single-instance deployments
- ❌ Requires session affinity for load balancing
- ❌ Not suitable for horizontal scaling

**Use Cases:**
- Single Docker container
- Development/testing
- Low-traffic production (single instance)

**Configuration:**
```bash
# .env
MCP_HTTP_STATELESS=false
```

**Load Balancer Configuration (if needed):**
```nginx
# nginx - sticky sessions
upstream mcp_backend {
    ip_hash;  # Session affinity based on client IP
    server mcp-server-1:8000;
    server mcp-server-2:8000;
}
```

---

### Stateless Mode

**Characteristics:**
- ✅ No session state stored
- ✅ Horizontal scaling without session affinity
- ✅ Suitable for Kubernetes deployments
- ⚠️ Slightly higher overhead (session recreation)

**Use Cases:**
- Kubernetes with multiple replicas
- High-availability deployments
- Auto-scaling environments

**Configuration:**
```bash
# .env
MCP_HTTP_STATELESS=true
```

**Kubernetes Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-arangodb-async
spec:
  replicas: 3  # Multiple instances
  selector:
    matchLabels:
      app: mcp-arangodb-async
  template:
    spec:
      containers:
      - name: mcp-server
        image: mcp-arangodb-async:latest
        env:
        - name: MCP_HTTP_STATELESS
          value: "true"  # Stateless mode
```

---

## CORS Configuration

### Why CORS Matters

Browser-based clients require CORS headers to access the MCP server from different origins.

### Critical Header: Mcp-Session-Id

**The `Mcp-Session-Id` header MUST be exposed for browser clients:**

```python
app = CORSMiddleware(
    app,
    allow_origins=cors_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],  # CRITICAL!
)
```

**Without this header:**
- Browser clients cannot read session ID
- Session management fails
- MCP protocol breaks

---

### CORS Configuration Examples

**Development (Allow All Origins):**
```bash
# .env
MCP_HTTP_CORS_ORIGINS=*
```

**Production (Specific Origins):**
```bash
# .env
MCP_HTTP_CORS_ORIGINS=https://app.example.com,https://admin.example.com
```

**Multiple Localhost Ports (Development):**
```bash
# .env
MCP_HTTP_CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8080
```

---

## Deployment

### Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  arangodb:
    image: arangodb:3.11
    environment:
      ARANGO_ROOT_PASSWORD: ${ARANGO_ROOT_PASSWORD}
    ports:
      - "8529:8529"
    volumes:
      - arango_data:/var/lib/arangodb3
    healthcheck:
      test: ["CMD", "arangosh", "--server.username", "root", "--server.password", "$ARANGO_ROOT_PASSWORD", "--javascript.execute-string", "db._version()"]
      interval: 10s
      timeout: 5s
      retries: 5

  mcp-server:
    build: .
    depends_on:
      arangodb:
        condition: service_healthy
    environment:
      ARANGO_URL: http://arangodb:8529
      ARANGO_DB: mcp_arangodb_test
      ARANGO_USERNAME: mcp_arangodb_user
      ARANGO_PASSWORD: ${ARANGO_PASSWORD}
      MCP_TRANSPORT: http
      MCP_HTTP_HOST: 0.0.0.0
      MCP_HTTP_PORT: 8000
      MCP_HTTP_STATELESS: false
      MCP_HTTP_CORS_ORIGINS: "*"
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  arango_data:
```

**Start:**
```powershell
docker compose up -d
```

**Test:**
```powershell
curl http://localhost:8000/health
```

---

### Kubernetes

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-arangodb-async
  labels:
    app: mcp-arangodb-async
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-arangodb-async
  template:
    metadata:
      labels:
        app: mcp-arangodb-async
    spec:
      containers:
      - name: mcp-server
        image: mcp-arangodb-async:0.2.7
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ARANGO_URL
          value: "http://arangodb-service:8529"
        - name: ARANGO_DB
          value: "mcp_arangodb_prod"
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
        - name: MCP_TRANSPORT
          value: "http"
        - name: MCP_HTTP_HOST
          value: "0.0.0.0"
        - name: MCP_HTTP_PORT
          value: "8000"
        - name: MCP_HTTP_STATELESS
          value: "true"  # Stateless for horizontal scaling
        - name: MCP_HTTP_CORS_ORIGINS
          value: "https://app.example.com"
        - name: LOG_LEVEL
          value: "INFO"
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
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-arangodb-async
spec:
  selector:
    app: mcp-arangodb-async
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Deploy:**
```bash
kubectl apply -f deployment.yaml
```

---

## Security Considerations

### 1. TLS/HTTPS

**Always use HTTPS in production:**

**Option A: Reverse Proxy (Recommended)**
```nginx
server {
    listen 443 ssl http2;
    server_name mcp.example.com;
    
    ssl_certificate /etc/ssl/certs/mcp.example.com.crt;
    ssl_certificate_key /etc/ssl/private/mcp.example.com.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Option B: Kubernetes Ingress**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mcp-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - mcp.example.com
    secretName: mcp-tls
  rules:
  - host: mcp.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mcp-arangodb-async
            port:
              number: 80
```

---

### 2. Authentication

**Implement authentication at reverse proxy level:**

```nginx
# Basic Auth
location / {
    auth_basic "MCP Server";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000;
}

# OAuth2 Proxy
location / {
    auth_request /oauth2/auth;
    proxy_pass http://localhost:8000;
}
```

---

### 3. Rate Limiting

**Prevent abuse:**

```nginx
# nginx rate limiting
limit_req_zone $binary_remote_addr zone=mcp_limit:10m rate=10r/s;

location / {
    limit_req zone=mcp_limit burst=20 nodelay;
    proxy_pass http://localhost:8000;
}
```

---

### 4. Firewall Rules

**Restrict access:**

```bash
# Allow only specific IPs
iptables -A INPUT -p tcp --dport 8000 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

---

## Migration from stdio

### Step 1: Update Environment Variables

```bash
# Before (stdio)
MCP_TRANSPORT=stdio

# After (HTTP)
MCP_TRANSPORT=http
MCP_HTTP_HOST=0.0.0.0
MCP_HTTP_PORT=8000
MCP_HTTP_STATELESS=false
MCP_HTTP_CORS_ORIGINS=*
```

### Step 2: Update Client Code

**Before (stdio - not applicable for HTTP):**
```json
{
  "mcpServers": {
    "arangodb": {
      "command": "python",
      "args": ["-m", "mcp_arangodb_async"]
    }
  }
}
```

**After (HTTP - JavaScript client):**
```javascript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamable-http.js";

const transport = new StreamableHTTPClientTransport({
  url: "http://localhost:8000/mcp"
});

const client = new Client({
  name: "my-client",
  version: "1.0.0"
}, {
  capabilities: {}
});

await client.connect(transport);
```

### Step 3: Test

```powershell
# Test health endpoint
curl http://localhost:8000/health

# Test MCP endpoint (requires MCP client)
```

---

## Client Configuration Examples

### LM Studio

```json
{
  "mcpServers": {
    "mcp_arangodb_async": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Gemini CLI

```json
{
  "mcpServers": {
    "mcp_arangodb_async": {
      "httpUrl": "http://localhost:8000/mcp"
    }
  }
}
```

---

## Related Documentation

- [Architecture Overview](architecture.md)
- [Transport Configuration](../configuration/transport-configuration.md)
- [Environment Variables](../configuration/environment-variables.md)
- [Low-Level MCP Rationale](low-level-mcp-rationale.md)