# First Interaction Guide

Test prompts and examples to verify your mcp-arangodb-async server is working correctly, with a focus on AI-Coding and software engineering use cases.

**Audience:** End Users (completed quickstart)  
**Prerequisites:** Server installed and configured, MCP client connected  
**Estimated Time:** 10-15 minutes

---

## What You'll Learn

This guide provides:
- **Verification prompts** to test server connectivity
- **AI-Coding examples** adapted to software engineering workflows
- **Progressive complexity** from simple queries to graph operations
- **Expected results** for each test

---

## Basic Verification Tests

### Test 1: List Collections

**Prompt:**
```
List all collections in my database.
```

**What This Tests:**
- Server connectivity
- Database access
- Basic tool execution (`arango_list_collections`)

**Expected Result:**
```json
["tests", "users", "products"]
```

**If It Fails:**
- Check server is running: `python -m mcp_arangodb_async --health`
- Verify MCP client configuration
- Check ArangoDB container: `docker compose ps`

---

### Test 2: Insert Document

**Prompt:**
```
Use arango_insert to add a document with name='test_document' and value=1 to a collection named 'tests'.
```

**What This Tests:**
- Write operations
- Collection creation (if doesn't exist)
- Document insertion (`arango_insert`)

**Expected Result:**
```json
{
  "_key": "12345",
  "_id": "tests/12345",
  "_rev": "_abc123",
  "name": "test_document",
  "value": 1
}
```

**Key Takeaway:** ArangoDB automatically generates `_key`, `_id`, and `_rev` fields.

---

### Test 3: Query Data

**Prompt:**
```
Query the tests collection and return all documents where value is greater than 0.
```

**What This Tests:**
- AQL query execution (`arango_query`)
- Filtering and result formatting

**Expected Result:**
```json
[
  {
    "_key": "12345",
    "_id": "tests/12345",
    "_rev": "_abc123",
    "name": "test_document",
    "value": 1
  }
]
```

---

## AI-Coding Use Cases

### Use Case 1: Codebase Dependency Graph

**Scenario:** Model Python module dependencies to detect circular imports.

**Prompt:**
```
Create a graph called 'codebase_graph' with:
- Vertex collection 'modules' for Python files
- Edge collection 'imports' for import relationships

Then insert these modules:
- auth.py (250 lines)
- database.py (180 lines)
- models.py (320 lines)

And these import relationships:
- auth imports database
- database imports models
- models imports auth (circular!)
```

**What This Tests:**
- Graph creation (`arango_create_graph`)
- Vertex insertion (`arango_insert`)
- Edge insertion (`arango_add_edge`)

**Expected Behavior:**
- Creates graph with proper edge definitions
- Inserts 3 vertices and 3 edges
- Returns confirmation for each operation

**Follow-up Prompt:**
```
Find circular dependencies by traversing from auth.py and detecting cycles.
```

**Expected Result:**
```json
{
  "cycle": ["modules/auth", "modules/database", "modules/models", "modules/auth"],
  "length": 4
}
```

**Key Takeaway:** Graph databases excel at detecting circular dependencies that are difficult to find with traditional tools.

---

### Use Case 2: API Endpoint Evolution

**Scenario:** Track API endpoint changes across versions to identify breaking changes.

**Prompt:**
```
Create a graph called 'api_evolution' with:
- Vertex collection 'endpoints' for API routes
- Edge collection 'replaces' for version transitions

Insert these endpoints:
- /api/v1/users (deprecated)
- /api/v2/users (current)
- /api/v2/users/{id} (current)

And these relationships:
- v2/users replaces v1/users
```

**What This Tests:**
- Multi-version data modeling
- Edge semantics (replaces, deprecates)
- Historical tracking

**Follow-up Prompt:**
```
Find all deprecated endpoints by querying edges with type='replaces'.
```

**Expected Result:**
```json
[
  {
    "old": "/api/v1/users",
    "new": "/api/v2/users",
    "breaking_change": true
  }
]
```

---

### Use Case 3: Microservices Communication

**Scenario:** Model service-to-service communication to optimize latency.

**Prompt:**
```
Create a graph called 'microservices' with:
- Vertex collection 'services' for microservices
- Edge collection 'api_calls' for service communication

Insert these services:
- auth-service (port 8001)
- user-service (port 8002)
- payment-service (port 8003)

And these API calls:
- user-service calls auth-service (latency: 50ms)
- payment-service calls user-service (latency: 30ms)
- payment-service calls auth-service (latency: 45ms)
```

**What This Tests:**
- Weighted edges (latency)
- Multi-hop traversal
- Path optimization

**Follow-up Prompt:**
```
Find the shortest path from payment-service to auth-service and calculate total latency.
```

**Expected Result:**
```json
{
  "path": ["payment-service", "auth-service"],
  "total_latency_ms": 45,
  "hops": 1
}
```

**Key Takeaway:** Direct communication is faster than multi-hop paths.

---

### Use Case 4: Test Coverage Mapping

**Scenario:** Map test files to source files to identify untested code.

**Prompt:**
```
Create a graph called 'test_coverage' with:
- Vertex collection 'source_files' for Python modules
- Vertex collection 'test_files' for test modules
- Edge collection 'tests' for coverage relationships

Insert source files:
- src/auth.py (250 lines)
- src/database.py (180 lines)
- src/models.py (320 lines)

Insert test files:
- tests/test_auth.py (150 lines)
- tests/test_database.py (120 lines)

And coverage edges:
- test_auth.py tests auth.py
- test_database.py tests database.py
```

**What This Tests:**
- Heterogeneous vertex collections
- Coverage analysis
- Gap detection

**Follow-up Prompt:**
```
Find all source files without test coverage by querying for vertices with no incoming 'tests' edges.
```

**Expected Result:**
```json
[
  {
    "file": "src/models.py",
    "lines": 320,
    "coverage": "none"
  }
]
```

**Key Takeaway:** Graph queries make it easy to find untested code paths.

---

### Use Case 5: Deployment Pipeline

**Scenario:** Model CI/CD pipeline stages to identify bottlenecks.

**Prompt:**
```
Create a graph called 'deployment_pipeline' with:
- Vertex collection 'stages' for pipeline stages
- Edge collection 'depends_on' for stage dependencies

Insert stages:
- build (duration: 120s)
- test (duration: 300s)
- deploy-staging (duration: 60s)
- deploy-production (duration: 90s)

And dependencies:
- test depends_on build
- deploy-staging depends_on test
- deploy-production depends_on deploy-staging
```

**What This Tests:**
- DAG (Directed Acyclic Graph) modeling
- Critical path analysis
- Duration aggregation

**Follow-up Prompt:**
```
Calculate the critical path from build to deploy-production and total duration.
```

**Expected Result:**
```json
{
  "critical_path": ["build", "test", "deploy-staging", "deploy-production"],
  "total_duration_seconds": 570,
  "bottleneck": "test"
}
```

**Key Takeaway:** The test stage is the bottleneck (300s out of 570s total).

---

## Advanced Verification Tests

### Test 4: Bulk Operations

**Prompt:**
```
Use arango_bulk_insert to insert 100 documents into a collection named 'performance_test' with fields: id (1-100), timestamp (current), and status ('active').
```

**What This Tests:**
- Bulk insertion performance
- Large dataset handling

**Expected Result:**
```json
{
  "inserted": 100,
  "errors": 0,
  "collection": "performance_test"
}
```

---

### Test 5: Index Creation

**Prompt:**
```
Create a hash index on the 'name' field of the 'tests' collection to improve query performance.
```

**What This Tests:**
- Index management (`arango_create_index`)
- Performance optimization

**Expected Result:**
```json
{
  "id": "tests/12345",
  "type": "hash",
  "fields": ["name"],
  "unique": false
}
```

---

## Troubleshooting Test Failures

### Tool Not Found

**Symptom:** MCP client reports "tool not found"

**Solutions:**
1. Verify server is running: `python -m mcp_arangodb_async --health`
2. Check toolset configuration: `MCP_COMPAT_TOOLSET=full` in `.env`
3. Restart MCP client after configuration changes

### Query Syntax Error

**Symptom:** AQL query fails with syntax error

**Solutions:**
1. Check AQL syntax in [ArangoDB documentation](https://docs.arangodb.com/stable/aql/)
2. Use bind variables for dynamic values
3. Test query in ArangoDB web UI first: http://localhost:8529

### Graph Already Exists

**Symptom:** Graph creation fails with "already exists" error

**Solutions:**
1. Drop existing graph first: Use `arango_query` with `FOR g IN _graphs FILTER g._key == 'graph_name' REMOVE g IN _graphs`
2. Use unique graph names for each test
3. Clean up test data between runs

---

## Next Steps

✅ **Your server is working correctly!**

**Explore More:**
- [Tools Reference](../user-guide/tools-reference.md) - Complete documentation for all 34 tools
- [Graph Operations Guide](../user-guide/graph-operations.md) - Advanced graph modeling patterns
- [Codebase Analysis Example](../examples/codebase-analysis.md) - Comprehensive real-world example

---

## Related Documentation
- [Quickstart Guide (stdio)](quickstart-stdio.md)
- [Installation Guide](installation.md)
- [Tools Reference](../user-guide/tools-reference.md)
- [Troubleshooting](../user-guide/troubleshooting.md)

