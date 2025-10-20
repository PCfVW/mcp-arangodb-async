# Documentation Style Guide
# mcp-arangodb-async Project

**Version:** 1.0  
**Date:** October 20, 2025  
**Status:** Authoritative Reference  
**Scope:** All documentation files in `docs/` and root `README.md`

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Voice, Tone, and Pedagogical Approach](#voice-tone-and-pedagogical-approach)
3. [Document Structure and Organization](#document-structure-and-organization)
4. [Terminology Standards](#terminology-standards)
5. [Code Examples and Technical Content](#code-examples-and-technical-content)
6. [Markdown Formatting Standards](#markdown-formatting-standards)
7. [Cross-Linking and Navigation](#cross-linking-and-navigation)
8. [AI-Coding Context Examples](#ai-coding-context-examples)
9. [Quick Reference Checklist](#quick-reference-checklist)

---

## Core Principles

### Pedagogical First
Every document must **teach**, not just inform. Readers should understand:
- **What** the feature/concept is
- **Why** it exists or matters
- **How** to use it effectively
- **When** to use it (and when not to)

### Actionable Content
Every section should enable immediate action:
- ✅ **Good:** "Run `docker compose up -d` to start ArangoDB"
- ❌ **Bad:** "ArangoDB can be started using Docker Compose"

### Progressive Disclosure
Information complexity increases gradually:
- **Beginner content:** Simple, concrete, step-by-step
- **Intermediate content:** Concepts, patterns, trade-offs
- **Advanced content:** Architecture, rationale, customization

### Context-Aware
Adapt examples to **AI-Coding and AI-Software Engineering workflows**:
- Use codebase analysis, dependency graphs, API modeling
- Avoid generic examples (jazz, travel, spatial data)
- Show real-world software engineering use cases

---

## Voice, Tone, and Pedagogical Approach

### Voice Standards

**Use Active Voice**
- ✅ **Correct:** "The server validates arguments using Pydantic models"
- ❌ **Incorrect:** "Arguments are validated by Pydantic models"

**Use Present Tense**
- ✅ **Correct:** "The tool returns a list of collections"
- ❌ **Incorrect:** "The tool will return a list of collections"

**Use Direct Address (Second Person)**
- ✅ **Correct:** "You can configure the transport using environment variables"
- ❌ **Incorrect:** "Users can configure the transport" or "One can configure"

**Use Imperative Mood for Instructions**
- ✅ **Correct:** "Install Docker Desktop before proceeding"
- ❌ **Incorrect:** "Docker Desktop should be installed"

### Tone Standards

**Be Clear and Precise**
- Avoid ambiguity and vague language
- Use specific version numbers, file paths, command syntax
- Define technical terms on first use

**Be Concise**
- One idea per paragraph
- Short sentences (15-20 words average)
- Remove unnecessary words

**Be Helpful, Not Condescending**
- ✅ **Correct:** "This step ensures database connectivity"
- ❌ **Incorrect:** "Obviously, you need to connect to the database"

**Be Honest About Trade-offs**
- Acknowledge limitations and alternatives
- Explain why decisions were made
- Show what users give up and gain

### Pedagogical Patterns

**Pattern 1: Context → Concept → Code → Conclusion**
```markdown
## Feature Name

### Why This Matters (Context)
Explain the problem or need this feature addresses.

### How It Works (Concept)
Explain the underlying concept or mechanism.

### Using the Feature (Code)
Provide concrete, runnable examples.

### Key Takeaways (Conclusion)
Summarize what users should remember.
```

**Pattern 2: Problem → Solution → Rationale**
```markdown
### The Challenge
Describe the specific problem.

### Our Solution
Show the implementation with code.

### Why This Approach
Explain the reasoning and trade-offs.
```

**Pattern 3: Before → After → Migration**
```markdown
### Old Approach
Show the previous way (if applicable).

### New Approach
Show the current/recommended way.

### Migration Guide
Provide step-by-step transition instructions.
```

---

## Document Structure and Organization

### File Naming Conventions

**Use Lowercase with Hyphens**
- ✅ **Correct:** `transport-configuration.md`, `low-level-mcp-rationale.md`
- ❌ **Incorrect:** `TransportConfiguration.md`, `transport_configuration.md`

**Use Descriptive Names**
- ✅ **Correct:** `quickstart-stdio.md` (specific)
- ❌ **Incorrect:** `quickstart.md` (ambiguous)

**Special Files Use UPPERCASE**
- `README.md`, `STYLE_GUIDE.md`, `CHANGELOG.md`

### Heading Hierarchy

**H1 (`#`) - Document Title Only**
- One H1 per document
- Use title case
- Example: `# Installation Guide`

**H2 (`##`) - Major Sections**
- Use title case
- Example: `## Why ArangoDB 3.11?`

**H3 (`###`) - Subsections**
- Use title case
- Example: `### Step-by-Step Installation`

**H4 (`####`) - Sub-subsections**
- Use title case
- Limit use; prefer flatter structure
- Example: `#### 1. Install Docker Desktop`

**Never Use H5 or H6**
- If you need this depth, restructure the document

### Heading Capitalization Rules

**Title Case for All Headings**
- Capitalize: First word, last word, all major words
- Lowercase: Articles (a, an, the), conjunctions (and, but, or), prepositions <4 letters (in, on, at, to)
- ✅ **Correct:** `## Why Run ArangoDB in Docker?`
- ❌ **Incorrect:** `## Why run ArangoDB in docker?`

**Exceptions:**
- Technical terms keep their casing: `ArangoDB`, `FastMCP`, `HTTP`, `stdio`
- Code elements in headings use backticks: `## Using the \`arango_query\` Tool`

### Document Front Matter

**Every Document Starts With:**
```markdown
# Document Title

Brief 1-2 sentence description of what this document covers.

**Audience:** [End Users | Developers | Advanced Users]
**Prerequisites:** [List required knowledge/setup]
**Estimated Time:** [X minutes]

---
```

**Example:**
```markdown
# Installation Guide

Complete guide to installing ArangoDB 3.11 with Docker and configuring the mcp-arangodb-async server.

**Audience:** End Users (new to the project)
**Prerequisites:** Docker Desktop installed, basic command-line familiarity
**Estimated Time:** 15-20 minutes

---
```

### Section Organization Patterns

**Getting Started Documents:**
1. Overview (What you'll accomplish)
2. Prerequisites
3. Step-by-step instructions
4. Verification
5. Next steps

**Reference Documents:**
1. Overview
2. Quick reference table/list
3. Detailed descriptions (alphabetical or by category)
4. Examples
5. Related documentation

**Conceptual Documents:**
1. Introduction (Why this matters)
2. Core concepts
3. How it works
4. Trade-offs and alternatives
5. When to use
6. Related documentation

---

## Terminology Standards

### Project-Specific Terms

**Always Use These Exact Terms:**

| **Correct Term** | **Incorrect Alternatives** | **Context** |
|------------------|---------------------------|-------------|
| `mcp-arangodb-async` | mcp-arangodb, arangodb-mcp, MCP ArangoDB | Project name |
| `ArangoDB 3.11` | ArangoDB, ArangoDB 3.x, Arango | Always specify version |
| `stdio transport` | standard I/O, stdin/stdout, stdio | MCP transport type |
| `HTTP transport` | http, HTTP server, web transport | MCP transport type |
| `low-level Server` | low-level MCP Server, Server API | `mcp.server.lowlevel.Server` |
| `FastMCP` | fast-mcp, FastMCP framework | High-level MCP framework |
| `tool` | function, command, operation | MCP tool (not Python function) |
| `MCP client` | AI client, assistant, agent | Claude Desktop, Augment Code, etc. |
| `python-arango` | arango-python, ArangoDB driver | Official Python driver |
| `Docker Compose` | docker-compose, docker compose | Use capital C |

### MCP Protocol Terms

**Use Official MCP Terminology:**

| **Term** | **Definition** | **Usage** |
|----------|---------------|-----------|
| **MCP** | Model Context Protocol | Always capitalize; spell out on first use |
| **tool** | Callable function exposed via MCP | Not "command" or "operation" |
| **transport** | Communication layer (stdio or HTTP) | Not "protocol" or "interface" |
| **server** | MCP server implementation | This project |
| **client** | MCP client (Claude Desktop, etc.) | Not "user" or "assistant" |
| **resource** | Data exposed via MCP resources API | Not used in this project |
| **prompt** | Predefined prompt template | Not used in this project |
| **lifespan context** | Server-wide state during lifecycle | Technical term for developers |
| **request context** | Per-request state | Technical term for developers |

### ArangoDB Terms

**Use Official ArangoDB Terminology:**

| **Term** | **Definition** | **Usage** |
|----------|---------------|-----------|
| **AQL** | ArangoDB Query Language | Always uppercase |
| **collection** | ArangoDB collection (like a table) | Not "table" |
| **document** | JSON document in a collection | Not "record" or "row" |
| **edge** | Relationship document in edge collection | Not "relationship" alone |
| **vertex** | Node document in vertex collection | Not "node" alone |
| **graph** | Named graph with edge definitions | Not "network" |
| **edge collection** | Collection storing edges | Not "edge table" |
| **vertex collection** | Collection storing vertices | Not "node collection" |
| **edge definition** | Schema defining edge relationships | Technical term |
| **bind variable** | AQL query parameter | Not "parameter" or "variable" |
| **traversal** | Graph traversal operation | Not "walk" or "navigation" |

### Technical Terms

**Capitalization and Formatting:**

| **Term** | **Correct** | **Incorrect** | **Notes** |
|----------|------------|--------------|-----------|
| Docker | Docker | docker, DOCKER | Brand name |
| Docker Compose | Docker Compose | docker-compose, docker compose | Capital C |
| Python | Python | python, PYTHON | Language name |
| PowerShell | PowerShell | powershell, Powershell | Microsoft brand |
| Windows | Windows | windows | Operating system |
| JSON | JSON | json, Json | Always uppercase |
| YAML | YAML | yaml, Yaml | Always uppercase |
| HTTP | HTTP | http, Http | Protocol acronym |
| CORS | CORS | cors, Cors | Cross-Origin Resource Sharing |
| API | API | api, Api | Application Programming Interface |
| CLI | CLI | cli, Cli | Command-Line Interface |
| SDK | SDK | sdk, Sdk | Software Development Kit |
| Pydantic | Pydantic | pydantic | Library name |
| Starlette | Starlette | starlette | Library name |
| Uvicorn | Uvicorn | uvicorn | ASGI server name |

### Version Specifications

**Always Specify Versions When Relevant:**

- ✅ **Correct:** "ArangoDB 3.11 is the last version with Apache 2.0 license"
- ❌ **Incorrect:** "ArangoDB is Apache 2.0 licensed"

- ✅ **Correct:** "python-arango 8.x uses unified `add_index()` API"
- ❌ **Incorrect:** "python-arango uses `add_index()`"

- ✅ **Correct:** "Python 3.11+ is required"
- ❌ **Incorrect:** "Python 3 is required"

### Abbreviations and Acronyms

**First Use: Spell Out with Acronym**
- ✅ **Correct:** "Model Context Protocol (MCP)"
- Then use: "MCP" throughout the rest of the document

**Common Acronyms (No Need to Spell Out):**
- HTTP, JSON, YAML, API, CLI, SDK, URL, URI, CORS, SSL, TLS

**Project-Specific Acronyms (Always Spell Out First):**
- MCP (Model Context Protocol)
- AQL (ArangoDB Query Language)
- BUSL (Business Source License)

---

## Code Examples and Technical Content

### Code Block Formatting

**Always Use Language Tags**
````markdown
✅ Correct:
```python
async def example():
    pass
```

❌ Incorrect:
```
async def example():
    pass
```
````

**Supported Language Tags:**
- `python` - Python code
- `powershell` - PowerShell commands
- `bash` - Bash/shell commands
- `json` - JSON data
- `yaml` - YAML configuration
- `dotenv` - Environment variable files
- `markdown` - Markdown examples
- `aql` - ArangoDB Query Language
- `text` - Plain text output

### Command-Line Examples

**PowerShell Commands (Windows Default):**
```powershell
# Use PowerShell syntax by default
docker compose up -d
python -m mcp_arangodb_async --transport http
```

**Bash Commands (Linux/macOS):**
```bash
# Explicitly label as bash when needed
docker compose up -d
python -m mcp_arangodb_async --transport http
```

**Include Comments for Clarity:**
```powershell
# Start ArangoDB container
docker compose up -d arangodb

# Verify container is healthy
docker compose ps arangodb
```

### Python Code Examples

**Use Type Hints:**
```python
# ✅ Correct
async def call_tool(ctx: RequestContext, tool_name: str, arguments: dict) -> list[types.TextContent]:
    pass

# ❌ Incorrect
async def call_tool(ctx, tool_name, arguments):
    pass
```

**Use Async/Await Consistently:**
```python
# ✅ Correct - async function with await
async def query_database(db: StandardDatabase, query: str) -> list:
    cursor = await db.aql.execute(query)
    return [doc async for doc in cursor]

# ❌ Incorrect - mixing sync/async
def query_database(db, query):
    cursor = db.aql.execute(query)
    return list(cursor)
```

**Include Imports When Relevant:**
```python
# ✅ Correct - show imports for clarity
from arango import ArangoClient
from mcp.server.lowlevel import Server

client = ArangoClient(hosts="http://localhost:8529")

# ❌ Incorrect - missing context
client = ArangoClient(hosts="http://localhost:8529")
```

### Configuration Examples

**Environment Variables (.env format):**
```dotenv
# ArangoDB Connection
ARANGO_HOST=http://localhost:8529
ARANGO_DB_NAME=mcp_arangodb_test
ARANGO_USERNAME=mcp_arangodb_user
ARANGO_PASSWORD=mcp_arangodb_password

# MCP Transport
MCP_TRANSPORT=stdio
```

**YAML Configuration (docker-compose.yml):**
```yaml
services:
  arangodb:
    image: arangodb:3.11
    container_name: mcp_arangodb_test
    environment:
      ARANGO_ROOT_PASSWORD: ${ARANGO_ROOT_PASSWORD:-changeme}
    ports:
      - "8529:8529"
```

### AQL Query Examples

**Use AQL Language Tag:**
```aql
FOR file IN files
  FILTER file.language == "python" AND file.lines > 500
  SORT file.lines DESC
  RETURN {path: file.path, lines: file.lines}
```

**Include Bind Variables When Relevant:**
```python
# Python code showing AQL with bind variables
query = """
FOR doc IN @@collection
  FILTER doc.status == @status
  RETURN doc
"""

bind_vars = {
    "@collection": "users",
    "status": "active"
}

cursor = db.aql.execute(query, bind_vars=bind_vars)
```

### Output Examples

**Show Expected Output:**
```powershell
# Command
python -m mcp_arangodb_async --health

# Expected output:
# {"ok": true, "db": "mcp_arangodb_test", "user": "mcp_arangodb_user"}
```

**Use Comments for Output:**
```python
result = db.collection("users").count()
# Returns: 42
```

### Error Examples

**Show Common Errors and Solutions:**
```powershell
# ❌ Error
docker compose up -d
# Error: Cannot connect to the Docker daemon

# ✅ Solution
# 1. Start Docker Desktop
# 2. Wait for Docker to be ready
# 3. Retry the command
```

---

## Markdown Formatting Standards

### Lists

**Use Hyphens for Unordered Lists:**
```markdown
✅ Correct:
- First item
- Second item
- Third item

❌ Incorrect:
* First item
+ Second item
- Third item
```

**Use Numbers for Ordered Lists:**
```markdown
✅ Correct:
1. First step
2. Second step
3. Third step

❌ Incorrect (auto-numbering):
1. First step
1. Second step
1. Third step
```

**Nested Lists (2-Space Indentation):**
```markdown
- Top level
  - Nested level 1
    - Nested level 2
  - Back to nested level 1
- Back to top level
```

### Emphasis and Formatting

**Bold for UI Elements and Important Terms:**
- ✅ **Correct:** "Click the **Start** button"
- ✅ **Correct:** "The **lifespan context** stores server-wide state"

**Italic for Emphasis (Use Sparingly):**
- ✅ **Correct:** "This is *not* recommended for production"

**Code Formatting for Technical Elements:**
- File names: `README.md`, `docker-compose.yml`
- Commands: `docker compose up -d`
- Code elements: `arango_query`, `@register_tool()`
- Environment variables: `ARANGO_HOST`, `MCP_TRANSPORT`
- Parameters: `tool_name`, `bind_vars`

**Never Use ALL CAPS for Emphasis:**
- ❌ **Incorrect:** "This is VERY important"
- ✅ **Correct:** "This is **very important**"

### Tables

**Use Tables for Structured Comparisons:**
```markdown
| Feature | stdio | HTTP |
|---------|-------|------|
| **Best for** | Desktop clients | Web/container deployments |
| **Clients** | Claude Desktop, Augment Code | Browser-based, custom clients |
| **Deployment** | Local process | Docker, Kubernetes |
```

**Table Formatting Rules:**
- Left-align text columns
- Right-align number columns (use `:---:` or `---:`)
- Use bold for row headers in first column
- Keep column widths reasonable (wrap long text)

### Links

**Use Descriptive Link Text:**
- ✅ **Correct:** "See the [Installation Guide](installation.md) for setup instructions"
- ❌ **Incorrect:** "Click [here](installation.md) for setup"

**External Links Include Domain:**
- ✅ **Correct:** "[ArangoDB Documentation](https://docs.arangodb.com/)"
- ❌ **Incorrect:** "[Documentation](https://docs.arangodb.com/)"

### Admonitions and Callouts

**Use Emoji for Visual Callouts:**
```markdown
✅ **Recommended:** Use ArangoDB 3.11 for Apache 2.0 licensing

⚠️ **Warning:** Version 3.12+ uses Business Source License

❌ **Not Supported:** Stateless mode is not implemented

💡 **Tip:** Use bind variables to prevent AQL injection
```

**Standard Emoji:**
- ✅ Success, correct, recommended
- ❌ Error, incorrect, not supported
- ⚠️ Warning, caution, important
- 💡 Tip, hint, best practice
- 📝 Note, information
- 🔧 Configuration, setup
- 🚀 Performance, optimization

### Horizontal Rules

**Use Three Hyphens:**
```markdown
---
```

**When to Use:**
- Separate major document sections
- After front matter
- Before appendices or related documentation

**When Not to Use:**
- Between subsections (use headings instead)
- Multiple times in quick succession

---

## Cross-Linking and Navigation

### Links in Root README.md (PyPI Compatibility)

⚠️ **CRITICAL:** The root `README.md` must use **absolute GitHub URLs** for all documentation links.

**Why PyPI Compatibility Matters:**
- The mcp-arangodb-async package is published to PyPI
- PyPI renders `README.md` but does not host the repository structure
- Relative links like `docs/configuration/transport-configuration.md` will be broken on PyPI
- Users viewing the package on PyPI need working links to documentation

**Absolute URL Format:**
```markdown
✅ CORRECT (works on both GitHub and PyPI):
[Transport Configuration](https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/configuration/transport-configuration.md)

[Installation Guide](https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/getting-started/installation.md)

❌ WRONG (broken on PyPI):
[Transport Configuration](docs/configuration/transport-configuration.md)
[Installation Guide](docs/getting-started/installation.md)
```

**URL Template:**
```
https://github.com/[username]/[repo]/blob/[branch]/[path-to-file]
```

**For This Project:**
```
https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/[subdirectory]/[filename].md
```

**Examples:**
```markdown
# Getting Started Links
[Installation Guide](https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/getting-started/installation.md)
[Quickstart (stdio)](https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/getting-started/quickstart-stdio.md)

# Configuration Links
[Transport Configuration](https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/configuration/transport-configuration.md)
[Environment Variables](https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/configuration/environment-variables.md)

# User Guide Links
[Tools Reference](https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/user-guide/tools-reference.md)
[Troubleshooting](https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/user-guide/troubleshooting.md)
```

**Image Links (if any):**
```markdown
✅ CORRECT:
![Architecture Diagram](https://raw.githubusercontent.com/PCfVW/mcp-arangodb-async/master/docs/images/architecture.png)

❌ WRONG:
![Architecture Diagram](docs/images/architecture.png)
```

**Testing PyPI Links:**
1. Before publishing to PyPI, test on test.pypi.org
2. Verify all links work from the PyPI package page
3. Check that links point to the correct branch (usually `main` or `master`)

### Internal Links (Within docs/)

**Use Relative Paths:**
```markdown
✅ Correct (from docs/getting-started/installation.md):
See [Transport Configuration](../configuration/transport-configuration.md)

❌ Incorrect (absolute path):
See [Transport Configuration](/docs/configuration/transport-configuration.md)
```

**Why Relative Paths in docs/:**
- Maintainability: Links work locally and on GitHub
- Portability: Documentation can be moved or forked
- Simplicity: Shorter, cleaner links

**Link Path Patterns:**
- Same directory: `[Link Text](filename.md)`
- Parent directory: `[Link Text](../filename.md)`
- Sibling directory: `[Link Text](../other-dir/filename.md)`
- Child directory: `[Link Text](subdir/filename.md)`

### Anchor Links (Within Same Document)

**Use Lowercase with Hyphens:**
```markdown
✅ Correct:
[See Installation Steps](#step-by-step-installation)

## Step-by-Step Installation

❌ Incorrect:
[See Installation Steps](#Step-by-Step-Installation)
```

**Anchor Generation Rules:**
- Convert to lowercase
- Replace spaces with hyphens
- Remove special characters except hyphens
- Example: `## Why ArangoDB 3.11?` → `#why-arangodb-311`

### Cross-Reference Sections

**Every Document Ends With Related Documentation:**
```markdown
## Related Documentation
- [Installation Guide](../getting-started/installation.md)
- [Transport Configuration](../configuration/transport-configuration.md)
- [Architecture Overview](architecture.md)
```

**Organize by Relevance:**
1. Prerequisites (what to read before)
2. Related topics (same level)
3. Next steps (what to read after)
4. Advanced topics (deeper dives)

### Navigation Patterns

**Breadcrumb Navigation (Optional for Deep Docs):**
```markdown
[Home](../../README.md) > [Developer Guide](../README.md) > HTTP Transport
```

**"Next Steps" Sections:**
```markdown
## Next Steps
- [Configure Environment Variables](../configuration/environment-variables.md)
- [Run Your First Query](first-interaction.md)
- [Explore Graph Operations](../user-guide/graph-operations.md)
```

### Link Validation

**Before Publishing, Verify:**
- All internal links resolve correctly
- No broken anchor links
- External links are accessible
- Relative paths work from file location

---

## AI-Coding Context Examples

### Adaptation Principles

**Transform Generic Examples to Software Engineering Context:**

| **Generic Domain** | **AI-Coding Adaptation** |
|-------------------|-------------------------|
| Jazz music (artists, albums) | Codebase structure (modules, classes, functions) |
| Spatial data (missions, spacecraft) | Deployment pipeline (services, containers, databases) |
| Travel (cities, flights) | Microservices (services, APIs, data stores) |
| Social network (users, friendships) | Dependency graph (packages, imports, calls) |

### Example Transformation Pattern

**Generic Example (Jazz):**
```
"Build a piano-jazz knowledge graph of Artists, Albums, Sub-genres..."
```

**AI-Coding Adaptation:**
```
"Build a codebase architecture graph:
- Vertices: Modules, Classes, Functions
- Edges: Imports, Calls, Inherits
- Query: Find circular dependencies
- Analyze: Calculate coupling metrics"
```

### Standard AI-Coding Use Cases

**Use Case 1: Codebase Dependency Analysis**
```aql
// Find circular dependencies
FOR v, e, p IN 2..10 OUTBOUND 'modules/auth'
  GRAPH 'codebase_graph'
  FILTER p.vertices[0]._id == p.vertices[-1]._id
  RETURN p
```

**Use Case 2: API Evolution Tracking**
```
"Model API endpoints as vertices, track changes over time:
- Vertices: Endpoints, Parameters, Response Schemas
- Edges: Depends_On, Replaces, Deprecated_By
- Query: Find breaking changes between versions
- Analyze: Impact analysis for API consumers"
```

**Use Case 3: Test Coverage Mapping**
```
"Create a graph of test files and source files:
- Vertices: SourceFile, TestFile, Function
- Edges: Tests, Calls, Covers
- Query: Find untested code paths
- Analyze: Calculate coverage metrics per module"
```

**Use Case 4: Microservices Communication**
```
"Model microservices architecture:
- Vertices: Services, APIs, Data Stores
- Edges: API_Calls, Data_Flow, Depends_On
- Query: Optimize service communication paths
- Analyze: Calculate latency and identify bottlenecks"
```

**Use Case 5: Deployment Pipeline**
```
"Model software deployment pipeline:
- Vertices: Services, Containers, Databases, Environments
- Edges: Depends_On, Communicates_With, Deploys_To
- Query: Find critical path for deployment
- Analyze: Identify single points of failure"
```

### Example Structure in Documentation

**When Showing AI-Coding Examples:**
```markdown
### Example: Codebase Dependency Graph

**Scenario:** Analyze Python project dependencies to find circular imports.

**Graph Model:**
- **Vertices:** Python modules (files)
- **Edges:** Import relationships

**Sample Data:**
\```python
# Create vertex collection
db.create_collection("modules")

# Create edge collection
db.create_collection("imports", edge=True)

# Insert modules
db.collection("modules").insert_many([
    {"_key": "auth", "path": "src/auth.py", "lines": 250},
    {"_key": "database", "path": "src/database.py", "lines": 180},
    {"_key": "models", "path": "src/models.py", "lines": 320}
])

# Insert imports
db.collection("imports").insert_many([
    {"_from": "modules/auth", "_to": "modules/database"},
    {"_from": "modules/database", "_to": "modules/models"},
    {"_from": "modules/models", "_to": "modules/auth"}  # Circular!
])
\```

**Query for Circular Dependencies:**
\```aql
FOR v, e, p IN 2..10 OUTBOUND 'modules/auth'
  GRAPH 'codebase_graph'
  FILTER p.vertices[0]._id == p.vertices[-1]._id
  RETURN {
    cycle: p.vertices[*].path,
    length: LENGTH(p.vertices)
  }
\```

**Expected Result:**
\```json
[
  {
    "cycle": ["src/auth.py", "src/database.py", "src/models.py", "src/auth.py"],
    "length": 4
  }
]
\```

**Key Takeaway:** Graph databases excel at detecting circular dependencies that are difficult to find with traditional tools.
```

---

## Quick Reference Checklist

### Before Writing

- [ ] Identify document audience (end users, developers, advanced)
- [ ] Define learning objectives (what readers will accomplish)
- [ ] Choose appropriate pedagogical pattern
- [ ] Gather all technical details (versions, commands, file paths)
- [ ] Review related documentation for consistency

### While Writing

**Voice and Tone:**
- [ ] Use active voice
- [ ] Use present tense
- [ ] Use direct address (second person)
- [ ] Use imperative mood for instructions
- [ ] Be clear, concise, and helpful

**Structure:**
- [ ] Include document front matter (audience, prerequisites, time)
- [ ] Use proper heading hierarchy (H1 → H2 → H3 → H4)
- [ ] Follow title case for all headings
- [ ] Organize sections logically (simple → complex)
- [ ] Include "Related Documentation" section at end

**Terminology:**
- [ ] Use exact project terms (`mcp-arangodb-async`, `ArangoDB 3.11`)
- [ ] Use official MCP terms (`tool`, `transport`, `client`)
- [ ] Use official ArangoDB terms (`collection`, `document`, `edge`, `vertex`)
- [ ] Specify versions when relevant
- [ ] Spell out acronyms on first use

**Code Examples:**
- [ ] Use language tags for all code blocks
- [ ] Include type hints in Python code
- [ ] Show imports when relevant
- [ ] Include comments for clarity
- [ ] Show expected output
- [ ] Use PowerShell for Windows commands (default)

**Formatting:**
- [ ] Use hyphens for unordered lists
- [ ] Use numbers for ordered lists
- [ ] Use backticks for code elements
- [ ] Use bold for UI elements and important terms
- [ ] Use tables for structured comparisons
- [ ] Use emoji for visual callouts (✅ ❌ ⚠️ 💡)

**PyPI Compatibility (Root README.md only):**
- [ ] All documentation links use absolute GitHub URLs
- [ ] All image links (if any) use absolute GitHub URLs
- [ ] URL format: `https://github.com/PCfVW/mcp-arangodb-async/blob/master/...`
- [ ] No relative paths in root README.md

**AI-Coding Context:**
- [ ] Adapt examples to software engineering workflows
- [ ] Use codebase analysis, dependency graphs, API modeling
- [ ] Avoid generic examples (jazz, travel, spatial)
- [ ] Show real-world use cases

### After Writing

**Content Review:**
- [ ] Every section is actionable
- [ ] Complexity increases gradually
- [ ] Trade-offs are acknowledged
- [ ] Examples are complete and runnable
- [ ] Technical details are accurate

**Link Validation:**
- [ ] All internal links work (relative paths in docs/)
- [ ] All anchor links work (lowercase with hyphens)
- [ ] External links are accessible
- [ ] "Related Documentation" section is complete
- [ ] **Root README.md uses absolute GitHub URLs** (PyPI compatibility)
- [ ] Test README.md rendering on test.pypi.org (if applicable)

**Formatting Check:**
- [ ] One H1 per document
- [ ] Consistent heading capitalization
- [ ] Code blocks have language tags
- [ ] Tables are properly formatted
- [ ] Lists use consistent markers

**Terminology Check:**
- [ ] Project terms are exact (`mcp-arangodb-async`, `ArangoDB 3.11`)
- [ ] MCP terms are official (`tool`, `transport`, `stdio transport`, `HTTP transport`)
- [ ] ArangoDB terms are official (`collection`, `document`, `edge`, `vertex`)
- [ ] Technical terms are capitalized correctly (`Docker`, `Python`, `JSON`)
- [ ] Versions are specified where relevant

**Final Polish:**
- [ ] Remove unnecessary words
- [ ] Check for typos and grammar
- [ ] Verify code examples are correct
- [ ] Test commands on target platform
- [ ] Read aloud for flow and clarity

---

## Document Metadata

**Style Guide Version:** 1.0
**Last Updated:** October 20, 2025
**Maintained By:** Project maintainers
**Feedback:** Submit issues or PRs to improve this guide

**Related Documentation:**
- [Pedagogical Documentation Roadmap](../PEDAGOGICAL_DOCUMENTATION_ROADMAP.md)
- [Documentation Improvement Plan](../DOCUMENTATION_IMPROVEMENT_PLAN.md)
- [README.md](../README.md)

---

## Appendix: Common Mistakes

### Mistake 1: Vague Instructions
❌ **Bad:** "Configure the database"
✅ **Good:** "Edit `.env` and set `ARANGO_DB_NAME=mcp_arangodb_test`"

### Mistake 2: Missing Context
❌ **Bad:** "Run the command"
✅ **Good:** "Run `docker compose up -d` to start the ArangoDB container"

### Mistake 3: Inconsistent Terminology
❌ **Bad:** "Use the arango_query function"
✅ **Good:** "Use the `arango_query` tool"

### Mistake 4: No Expected Output
❌ **Bad:** "Run the health check"
✅ **Good:**
```powershell
python -m mcp_arangodb_async --health
# Expected: {"ok": true, "db": "mcp_arangodb_test"}
```

### Mistake 5: Generic Examples
❌ **Bad:** "Build a jazz music knowledge graph"
✅ **Good:** "Build a codebase dependency graph to find circular imports"

### Mistake 6: Passive Voice
❌ **Bad:** "The tool is used to query the database"
✅ **Good:** "Use the `arango_query` tool to query the database"

### Mistake 7: Future Tense
❌ **Bad:** "The server will validate the arguments"
✅ **Good:** "The server validates the arguments"

### Mistake 8: Missing Version
❌ **Bad:** "Install ArangoDB"
✅ **Good:** "Install ArangoDB 3.11"

### Mistake 9: Ambiguous Links
❌ **Bad:** "Click [here](installation.md)"
✅ **Good:** "See the [Installation Guide](installation.md)"

### Mistake 10: No Trade-off Discussion
❌ **Bad:** "Use FastMCP for better performance"
✅ **Good:** "FastMCP simplifies tool registration but lacks advanced lifecycle control. Use low-level Server when you need custom startup logic."

### Mistake 11: Relative Links in Root README.md
❌ **Bad (broken on PyPI):**
```markdown
[Installation Guide](docs/getting-started/installation.md)
```
✅ **Good (works on PyPI):**
```markdown
[Installation Guide](https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/getting-started/installation.md)
```

### Mistake 12: Absolute Links in docs/ Files
❌ **Bad (hard to maintain):**
```markdown
# In docs/getting-started/installation.md
[Transport Configuration](https://github.com/PCfVW/mcp-arangodb-async/blob/master/docs/configuration/transport-configuration.md)
```
✅ **Good (maintainable):**
```markdown
# In docs/getting-started/installation.md
[Transport Configuration](../configuration/transport-configuration.md)
```

---

**End of Style Guide**

