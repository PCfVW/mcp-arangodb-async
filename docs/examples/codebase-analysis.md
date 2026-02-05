# Example: Codebase Dependency Analysis

A sophisticated example demonstrating how to model and analyze a Python codebase using ArangoDB's graph capabilities.

**Audience:** Developers and Software Architects  
**Prerequisites:** Understanding of Python, software dependencies, and graph concepts  
**Estimated Time:** 45-60 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [Problem Statement](#problem-statement)
3. [Graph Model Design](#graph-model-design)
4. [Implementation Steps](#implementation-steps)
5. [Analysis Queries](#analysis-queries)
6. [Advanced Use Cases](#advanced-use-cases)
7. [Related Documentation](#related-documentation)

---

## Overview

### What You'll Learn

✅ **Graph Modeling** - Design a graph schema for codebase structure  
✅ **Data Import** - Populate graph with codebase metadata  
✅ **Dependency Analysis** - Find direct and transitive dependencies  
✅ **Circular Detection** - Identify circular dependencies  
✅ **Impact Analysis** - Determine change impact radius  
✅ **Architecture Visualization** - Export graph for visualization

### Why Use Graphs for Codebase Analysis?

**Traditional Approach (Text Search):**
```bash
# Find what imports module X
grep -r "import auth" src/
# ❌ Misses indirect dependencies
# ❌ Can't detect circular dependencies
# ❌ No visualization of architecture
```

**Graph Approach (ArangoDB):**
```python
# Find all dependencies (direct + transitive)
FOR v, e, p IN 1..10 OUTBOUND 'modules/auth' calls
  RETURN p
# ✅ Finds all transitive dependencies
# ✅ Detects circular dependencies
# ✅ Visualizes architecture
```

---

## Problem Statement

### Scenario

You're working on a Python project with 50+ modules and 200+ functions. You need to:

1. **Understand Dependencies** - Which modules depend on `auth.py`?
2. **Detect Circular Dependencies** - Are there any circular imports?
3. **Impact Analysis** - If I change `database.py`, what breaks?
4. **Refactoring Safety** - Can I safely move `utils.py` to a different package?
5. **Architecture Documentation** - Generate a dependency diagram

### Traditional Tools Limitations

| Tool | Limitation |
|------|------------|
| **grep/ripgrep** | Only finds direct imports, no transitive analysis |
| **pylint** | Detects circular imports but no visualization |
| **pydeps** | Generates diagrams but limited query capabilities |
| **Static analyzers** | No runtime dependency tracking |

### Graph Database Advantages

✅ **Transitive Queries** - Find dependencies at any depth  
✅ **Circular Detection** - Built-in cycle detection  
✅ **Impact Analysis** - Reverse traversal for dependents  
✅ **Flexible Queries** - AQL for complex analysis  
✅ **Visualization** - Export to Graphviz, D3.js, etc.

---

## Graph Model Design

### Vertex Collections

**1. `modules` - Python modules/files**
```json
{
  "_key": "auth",
  "name": "auth.py",
  "path": "src/services/auth.py",
  "type": "module",
  "lines_of_code": 250,
  "functions_count": 12,
  "classes_count": 3
}
```

**2. `functions` - Functions and methods**
```json
{
  "_key": "authenticate_user",
  "name": "authenticate_user",
  "module": "auth",
  "signature": "authenticate_user(username: str, password: str) -> User",
  "lines_of_code": 25,
  "complexity": 5
}
```

**3. `classes` - Classes**
```json
{
  "_key": "UserService",
  "name": "UserService",
  "module": "auth",
  "methods_count": 8,
  "lines_of_code": 150
}
```

### Edge Collections

**1. `imports` - Module imports module**
```json
{
  "_from": "modules/api",
  "_to": "modules/auth",
  "import_type": "direct",
  "import_statement": "from services.auth import authenticate_user"
}
```

**2. `calls` - Function calls function**
```json
{
  "_from": "functions/login_handler",
  "_to": "functions/authenticate_user",
  "call_count": 3,
  "call_locations": ["api.py:45", "api.py:67", "api.py:89"]
}
```

**3. `contains` - Module contains function/class**
```json
{
  "_from": "modules/auth",
  "_to": "functions/authenticate_user",
  "relationship": "defines"
}
```

### Graph Schema

```
┌─────────────────────────────────────────────────────────────┐
│                     Codebase Graph                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌──────────┐         ┌─────────┐
   │ modules │          │functions │         │ classes │
   └─────────┘          └──────────┘         └─────────┘
        │                     │                     │
        │ imports             │ calls               │ inherits
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                        ┌──────────┐
                        │  Graph   │
                        │ "codebase"│
                        └──────────┘
```

---

## Implementation Steps

### Step 1: Create Graph Structure

**Prompt Claude:**
```
Create a graph called 'codebase' with:
- Vertex collections: 'modules', 'functions', 'classes'
- Edge collection: 'imports' (from modules to modules)
- Edge collection: 'calls' (from functions to functions)
- Edge collection: 'contains' (from modules to functions/classes)
```

**Expected MCP Tool Calls:**
1. `arango_create_graph` - Create named graph
2. `arango_add_vertex_collection` - Add vertex collections (3 calls)
3. `arango_add_edge_definition` - Add edge definitions (3 calls)

**Verification:**
```
List all graphs in the database
```

**Expected Output:**
```json
{
  "graphs": [
    {
      "name": "codebase",
      "edgeDefinitions": [
        {"collection": "imports", "from": ["modules"], "to": ["modules"]},
        {"collection": "calls", "from": ["functions"], "to": ["functions"]},
        {"collection": "contains", "from": ["modules"], "to": ["functions", "classes"]}
      ],
      "orphanCollections": []
    }
  ]
}
```

---

### Step 2: Import Module Data

**Prompt Claude:**
```
Insert these modules into the 'modules' collection:

1. auth.py (src/services/auth.py) - 250 lines, 12 functions, 3 classes
2. database.py (src/core/database.py) - 180 lines, 8 functions, 2 classes
3. api.py (src/api/api.py) - 320 lines, 15 functions, 5 classes
4. utils.py (src/utils/utils.py) - 120 lines, 20 functions, 0 classes
5. models.py (src/models/models.py) - 200 lines, 0 functions, 10 classes
```

**Expected MCP Tool Call:**
`arango_bulk_insert` with collection="modules"

**Sample Data:**
```json
[
  {
    "_key": "auth",
    "name": "auth.py",
    "path": "src/services/auth.py",
    "type": "module",
    "lines_of_code": 250,
    "functions_count": 12,
    "classes_count": 3
  },
  {
    "_key": "database",
    "name": "database.py",
    "path": "src/core/database.py",
    "type": "module",
    "lines_of_code": 180,
    "functions_count": 8,
    "classes_count": 2
  }
]
```

---

### Step 3: Import Function Data

**Prompt Claude:**
```
Insert these functions into the 'functions' collection:

auth.py functions:
- authenticate_user(username, password) -> User
- validate_token(token) -> bool
- refresh_token(user_id) -> str

database.py functions:
- connect() -> Connection
- execute_query(query) -> Result
- close_connection() -> None

api.py functions:
- login_handler(request) -> Response
- logout_handler(request) -> Response
- protected_endpoint(request) -> Response
```

**Expected MCP Tool Call:**
`arango_bulk_insert` with collection="functions"

---

### Step 4: Create Import Relationships

**Prompt Claude:**
```
Create import relationships in the 'imports' edge collection:

- api.py imports auth.py (direct import)
- api.py imports database.py (direct import)
- auth.py imports database.py (direct import)
- auth.py imports utils.py (direct import)
- database.py imports utils.py (direct import)
```

**Expected MCP Tool Call:**
`arango_bulk_insert` with collection="imports"

**Sample Data:**
```json
[
  {
    "_from": "modules/api",
    "_to": "modules/auth",
    "import_type": "direct",
    "import_statement": "from services.auth import authenticate_user"
  },
  {
    "_from": "modules/api",
    "_to": "modules/database",
    "import_type": "direct",
    "import_statement": "from core.database import execute_query"
  }
]
```

---

### Step 5: Create Function Call Relationships

**Prompt Claude:**
```
Create function call relationships in the 'calls' edge collection:

- login_handler calls authenticate_user (3 times)
- login_handler calls execute_query (1 time)
- authenticate_user calls validate_token (2 times)
- authenticate_user calls execute_query (1 time)
```

**Expected MCP Tool Call:**
`arango_bulk_insert` with collection="calls"

---

## Analysis Queries

### Query 1: Find Direct Dependencies

**Question:** What modules does `api.py` directly import?

**Prompt Claude:**
```
Find all modules that api.py directly imports using the codebase graph
```

**Expected AQL Query:**
```aql
FOR v IN 1..1 OUTBOUND 'modules/api' imports
  RETURN {
    module: v.name,
    path: v.path,
    lines_of_code: v.lines_of_code
  }
```

**Expected Result:**
```json
[
  {"module": "auth.py", "path": "src/services/auth.py", "lines_of_code": 250},
  {"module": "database.py", "path": "src/core/database.py", "lines_of_code": 180}
]
```

---

### Query 2: Find Transitive Dependencies

**Question:** What are ALL dependencies of `api.py` (direct + indirect)?

**Prompt Claude:**
```
Find all transitive dependencies of api.py (up to 10 levels deep)
```

**Expected AQL Query:**
```aql
FOR v, e, p IN 1..10 OUTBOUND 'modules/api' imports
  RETURN DISTINCT {
    module: v.name,
    path: v.path,
    depth: LENGTH(p.edges)
  }
```

**Expected Result:**
```json
[
  {"module": "auth.py", "path": "src/services/auth.py", "depth": 1},
  {"module": "database.py", "path": "src/core/database.py", "depth": 1},
  {"module": "utils.py", "path": "src/utils/utils.py", "depth": 2}
]
```

**Insight:** `api.py` depends on `utils.py` indirectly through `auth.py` and `database.py`.

---

### Query 3: Find Reverse Dependencies (Impact Analysis)

**Question:** If I change `database.py`, what modules are affected?

**Prompt Claude:**
```
Find all modules that depend on database.py (reverse traversal)
```

**Expected AQL Query:**
```aql
FOR v, e, p IN 1..10 INBOUND 'modules/database' imports
  RETURN DISTINCT {
    module: v.name,
    path: v.path,
    depth: LENGTH(p.edges)
  }
```

**Expected Result:**
```json
[
  {"module": "api.py", "path": "src/api/api.py", "depth": 1},
  {"module": "auth.py", "path": "src/services/auth.py", "depth": 1}
]
```

**Insight:** Changing `database.py` affects 2 modules directly.

---

### Query 4: Detect Circular Dependencies

**Question:** Are there any circular import dependencies?

**Prompt Claude:**
```
Check for circular dependencies in the codebase graph by finding cycles in the imports edge collection
```

**Expected AQL Query:**
```aql
FOR v, e, p IN 2..10 OUTBOUND 'modules/api' imports
  FILTER v._id == 'modules/api'
  RETURN {
    cycle: p.vertices[*].name,
    length: LENGTH(p.vertices)
  }
```

**Expected Result (No Cycles):**
```json
[]
```

**Expected Result (With Cycle):**
```json
[
  {
    "cycle": ["api.py", "auth.py", "models.py", "api.py"],
    "length": 4
  }
]
```

**Insight:** If result is empty, no circular dependencies exist. Otherwise, refactor to break cycles.

---

### Query 5: Find Leaf Modules (No Dependencies)

**Question:** Which modules have no dependencies (utility modules)?

**Prompt Claude:**
```
Find all modules that don't import any other modules (leaf nodes in the dependency graph)
```

**Expected AQL Query:**
```aql
FOR m IN modules
  LET outbound_count = LENGTH(
    FOR v IN 1..1 OUTBOUND m imports
      RETURN 1
  )
  FILTER outbound_count == 0
  RETURN {
    module: m.name,
    path: m.path,
    lines_of_code: m.lines_of_code
  }
```

**Expected Result:**
```json
[
  {"module": "utils.py", "path": "src/utils/utils.py", "lines_of_code": 120}
]
```

**Insight:** `utils.py` is a leaf module - safe to refactor without breaking dependencies.

---

## Advanced Use Cases

### Use Case 1: Dependency Depth Analysis

**Goal:** Find the maximum dependency depth for each module

**Prompt Claude:**
```
For each module, calculate the maximum dependency depth (longest path to a leaf module)
```

**Expected AQL Query:**
```aql
FOR m IN modules
  LET max_depth = (
    FOR v, e, p IN 1..10 OUTBOUND m imports
      RETURN LENGTH(p.edges)
  )
  RETURN {
    module: m.name,
    max_depth: MAX(max_depth) || 0
  }
```

**Expected Result:**
```json
[
  {"module": "api.py", "max_depth": 2},
  {"module": "auth.py", "max_depth": 1},
  {"module": "database.py", "max_depth": 1},
  {"module": "utils.py", "max_depth": 0}
]
```

---

### Use Case 2: Function Call Chain Analysis

**Goal:** Find the call chain from `login_handler` to `execute_query`

**Prompt Claude:**
```
Find all call paths from login_handler function to execute_query function
```

**Expected AQL Query:**
```aql
FOR v, e, p IN 1..5 OUTBOUND 'functions/login_handler' calls
  FILTER v._key == 'execute_query'
  RETURN {
    path: p.vertices[*].name,
    length: LENGTH(p.vertices)
  }
```

**Expected Result:**
```json
[
  {
    "path": ["login_handler", "authenticate_user", "execute_query"],
    "length": 3
  },
  {
    "path": ["login_handler", "execute_query"],
    "length": 2
  }
]
```

**Insight:** `login_handler` calls `execute_query` both directly and indirectly through `authenticate_user`.

---

### Use Case 3: Module Complexity Score

**Goal:** Calculate complexity score based on dependencies and dependents

**Prompt Claude:**
```
Calculate complexity score for each module:
- Score = (outbound_dependencies * 2) + (inbound_dependencies * 3) + (lines_of_code / 100)
```

**Expected AQL Query:**
```aql
FOR m IN modules
  LET outbound = LENGTH(FOR v IN 1..1 OUTBOUND m imports RETURN 1)
  LET inbound = LENGTH(FOR v IN 1..1 INBOUND m imports RETURN 1)
  LET complexity = (outbound * 2) + (inbound * 3) + (m.lines_of_code / 100)
  RETURN {
    module: m.name,
    outbound_deps: outbound,
    inbound_deps: inbound,
    lines_of_code: m.lines_of_code,
    complexity_score: complexity
  }
  SORT complexity DESC
```

**Expected Result:**
```json
[
  {"module": "database.py", "outbound_deps": 1, "inbound_deps": 2, "lines_of_code": 180, "complexity_score": 9.8},
  {"module": "auth.py", "outbound_deps": 2, "inbound_deps": 1, "lines_of_code": 250, "complexity_score": 9.5},
  {"module": "api.py", "outbound_deps": 2, "inbound_deps": 0, "lines_of_code": 320, "complexity_score": 7.2},
  {"module": "utils.py", "outbound_deps": 0, "inbound_deps": 2, "lines_of_code": 120, "complexity_score": 7.2}
]
```

**Insight:** `database.py` has highest complexity - prioritize for refactoring.

---

## Related Documentation

- [Graph Operations Tools](../user-guide/tools-reference.md#graph-management)
- [Graph Traversal Guide](../user-guide/tools-reference.md#graph-traversal)
- [AQL Query Examples](../getting-started/first-interaction.md)
- [Architecture Overview](../developer-guide/architecture.md)

