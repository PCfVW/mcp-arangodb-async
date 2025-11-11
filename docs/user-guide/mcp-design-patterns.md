# MCP Design Patterns

Comprehensive guide to using MCP Design Patterns for efficient tool management with mcp-arangodb-async.

**Audience:** Developers building AI agents and MCP clients  
**Prerequisites:** Understanding of MCP protocol, basic ArangoDB knowledge  
**Estimated Time:** 45-60 minutes

---

## Table of Contents

1. [Overview](#overview)
2. [Why Design Patterns Matter](#why-design-patterns-matter)
3. [Pattern 1: Progressive Tool Discovery](#pattern-1-progressive-tool-discovery)
4. [Pattern 2: Context Switching](#pattern-2-context-switching)
5. [Pattern 3: Tool Unloading](#pattern-3-tool-unloading)
6. [Combining Patterns](#combining-patterns)
7. [Best Practices](#best-practices)
8. [Related Documentation](#related-documentation)

---

## Overview

The mcp-arangodb-async server provides **43 MCP tools** across 9 categories. As AI agents scale to handle hundreds or thousands of tools across multiple MCP servers, loading all tool definitions upfront and passing intermediate results through the context window reduces efficiency and increases costs.

This guide explores three MCP design patterns that enable AI agents to interact with the server more efficiently:

1. **Progressive Tool Discovery** - Load tools on-demand based on task requirements
2. **Context Switching** - Switch between predefined tool sets for different workflows
3. **Tool Unloading** - Explicitly remove tool definitions to reduce cognitive load

These patterns are inspired by [Anthropic's research on code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp), which demonstrates how AI agents can reduce context overhead by up to **98.7%** through strategic tool management.

**Key Insight:** Rather than loading all 43 tools upfront (consuming ~150,000 tokens), AI agents can dynamically discover and load only the 3-5 tools needed for a specific task (~2,000 tokens).

---

## Why Design Patterns Matter

### The Challenge: Token Consumption at Scale

When an MCP server exposes dozens of tools, loading all tool definitions into the AI agent's context window consumes excessive tokens before the agent even reads the user's request.

**Without Design Patterns:**
- Load all 43 tool definitions upfront: ~150,000 tokens
- Every intermediate result passes through the model
- Large documents may exceed context window limits
- Increased latency and costs

**With Design Patterns:**
- Load only relevant tools: ~2,000 tokens (98.7% reduction)
- Process data in execution environment before returning to model
- Maintain focused, minimal tool sets per workflow
- Faster response times and lower costs

### Real-World Impact

**Example Workflow:** Analyze codebase dependencies and generate documentation

**Traditional Approach:**
```
1. Load all 43 tools → 150,000 tokens
2. Query modules collection → 10,000 rows through context
3. Filter in model → Process all rows
4. Generate graph → Full dataset through context
5. Export documentation → Large result through context
Total: ~200,000+ tokens
```

**Design Pattern Approach:**
```
1. Search for "graph" tools → Load 5 tools → 2,000 tokens
2. Query modules → Filter in code → Return 50 relevant rows
3. Generate graph → Process in execution environment
4. Export documentation → Return summary only
Total: ~5,000 tokens (97.5% reduction)
```

---

## Pattern 1: Progressive Tool Discovery

**Intent:** Dynamically search and load MCP tools based on keywords, criteria, or user needs rather than loading all tools upfront.

### How It Works

Progressive Tool Discovery allows AI agents to:
- Start with minimal context (just discovery mechanisms)
- Search for relevant tools based on task requirements
- Load only the tool definitions needed for the current workflow
- Reduce initial token consumption by 95%+

### Available Tools

#### arango_search_tools

Search for MCP tools by keywords and categories.

**Parameters:**
- `keywords` (array of strings, required) - Keywords to search for in tool names and descriptions
- `categories` (array of strings, optional) - Filter by categories: `core_data`, `indexing`, `validation`, `schema`, `query`, `graph_basic`, `graph_advanced`, `aliases`, `health`, `mcp_patterns`
- `detail_level` (string, optional) - Level of detail: `name` (just names), `summary` (names + descriptions), `full` (complete schemas). Default: `summary`

**Returns:**
- `matches` (array) - Matching tools with requested detail level
- `total_matches` (integer) - Number of matching tools
- `keywords` (array) - Keywords used in search
- `categories_searched` (string or array) - Categories searched
- `detail_level` (string) - Detail level returned

**Example:**
```json
{
  "keywords": ["graph", "traverse"],
  "categories": ["graph_basic"],
  "detail_level": "summary"
}
```

**Result:**
```json
{
  "matches": [
    {
      "name": "arango_traverse",
      "description": "Traverse graph from a start vertex with depth bounds"
    },
    {
      "name": "arango_shortest_path",
      "description": "Compute the shortest path between two vertices"
    }
  ],
  "total_matches": 2,
  "keywords": ["graph", "traverse"],
  "categories_searched": ["graph_basic"],
  "detail_level": "summary"
}
```

**Use Cases:**
- Discover graph tools when building dependency graphs
- Find query optimization tools for performance analysis
- Locate validation tools for data integrity checks
- Search for backup tools before data migration

#### arango_list_tools_by_category

List all MCP tools organized by category.

**Parameters:**
- `category` (string, optional) - Category to filter by. If not specified, returns all categories with their tools.

**Returns:**
- If category specified: `category`, `tools`, `tool_count`
- If no category: `categories` (object with all categories), `total_tools`

**Example:**
```json
{
  "category": "graph_basic"
}
```

**Result:**
```json
{
  "category": "graph_basic",
  "tools": [
    "arango_create_graph",
    "arango_list_graphs",
    "arango_add_vertex_collection",
    "arango_add_edge_definition",
    "arango_add_edge",
    "arango_traverse",
    "arango_shortest_path"
  ],
  "tool_count": 7
}
```

**Use Cases:**
- Understand tool organization before starting a workflow
- Explore available tools in a specific domain
- Build custom tool sets for specialized workflows
- Document available capabilities for team members

### Workflow Example

**Scenario:** Build a codebase dependency graph to find circular imports

**Step 1: Discover Graph Tools**
```
Agent: "I need to analyze code dependencies. Search for tools related to 'graph' and 'dependency'."

Call: arango_search_tools
Args: {"keywords": ["graph", "dependency"], "detail_level": "summary"}

Result: Found 12 tools including arango_create_graph, arango_traverse, arango_add_edge
```

**Step 2: Load Specific Tools**
```
Agent: "I need graph creation and traversal. Load full schemas for these tools."

Call: arango_search_tools
Args: {
  "keywords": ["create_graph", "traverse", "add_edge"],
  "detail_level": "full"
}

Result: Loaded 3 tools with complete schemas (~2,000 tokens)
```

**Step 3: Execute Workflow**
```
Agent: "Now I can create the graph and analyze dependencies."

Uses: arango_create_graph, arango_add_edge, arango_traverse
Result: Circular dependency detected in modules/auth → modules/database → modules/models → modules/auth
```

**Token Savings:** 148,000 tokens (98.7% reduction from loading all 43 tools)

### Best Practices

**Start Broad, Then Narrow:**
- Begin with category-based discovery to understand tool organization
- Use keyword search to find specific tools for your task
- Load full schemas only when ready to use the tools

**Use Appropriate Detail Levels:**
- `name`: Quick overview of available tools
- `summary`: Understand tool purposes before loading
- `full`: Ready to execute, need complete parameter schemas

**Cache Tool Definitions:**
- Once loaded, cache tool schemas for the session
- Avoid reloading the same tools multiple times
- Clear cache when switching to a different workflow

**Combine with Code Execution:**
- Use filesystem-based tool discovery (as described in Anthropic's article)
- Present tools as code APIs for even more efficient loading
- Filter and transform results in execution environment

---

## Pattern 2: Context Switching

**Intent:** Dynamically switch between predefined sets of MCP tools for different workflows or use cases.

### How It Works

Context Switching allows AI agents to:
- Define workflow-specific tool sets (contexts)
- Switch contexts based on task type
- Maintain focused, minimal tool sets per workflow
- Reduce cognitive load and improve tool selection accuracy

### Available Contexts

The server provides 6 predefined workflow contexts:

| Context | Tools | Use Case |
|---------|-------|----------|
| **baseline** | 7 | Minimal CRUD operations for basic database interaction |
| **data_analysis** | 7 | Query optimization and performance analysis |
| **graph_modeling** | 10 | Graph creation, traversal, and analysis |
| **bulk_operations** | 6 | Batch processing and bulk data operations |
| **schema_validation** | 6 | Data integrity and schema management |
| **full** | 43 | All available tools (fallback for complex workflows) |

### Available Tools

#### arango_switch_context

Switch to a different workflow context with a predefined set of tools.

**Parameters:**
- `context` (string, required) - Workflow context to switch to: `baseline`, `data_analysis`, `graph_modeling`, `bulk_operations`, `schema_validation`, `full`

**Returns:**
- `from_context` (string) - Previous context
- `to_context` (string) - New active context
- `description` (string) - Description of new context
- `tools_added` (array) - Tools added in new context
- `tools_removed` (array) - Tools removed from previous context
- `total_tools` (integer) - Total tools in new context
- `active_tools` (array) - All tools in new context

**Example:**
```json
{
  "context": "graph_modeling"
}
```

**Result:**
```json
{
  "from_context": "baseline",
  "to_context": "graph_modeling",
  "description": "Graph creation, traversal, and analysis",
  "tools_added": [
    "arango_create_graph",
    "arango_traverse",
    "arango_shortest_path"
  ],
  "tools_removed": [
    "arango_backup"
  ],
  "total_tools": 10,
  "active_tools": [
    "arango_create_graph",
    "arango_list_graphs",
    "arango_add_vertex_collection",
    "arango_add_edge_definition",
    "arango_add_edge",
    "arango_traverse",
    "arango_shortest_path",
    "arango_graph_statistics",
    "arango_validate_graph_integrity",
    "arango_query"
  ]
}
```

#### arango_get_active_context

Get the currently active workflow context and its tool set.

**Parameters:**
- None (empty object or omitted)

**Returns:**
- `active_context` (string) - Current context name
- `description` (string) - Context description
- `tools` (array) - Tools in current context
- `tool_count` (integer) - Number of tools

**Example:**
```json
{}
```

**Result:**
```json
{
  "active_context": "graph_modeling",
  "description": "Graph creation, traversal, and analysis",
  "tools": [
    "arango_create_graph",
    "arango_list_graphs",
    "arango_add_vertex_collection",
    "arango_add_edge_definition",
    "arango_add_edge",
    "arango_traverse",
    "arango_shortest_path",
    "arango_graph_statistics",
    "arango_validate_graph_integrity",
    "arango_query"
  ],
  "tool_count": 10
}
```

#### arango_list_contexts

List all available workflow contexts with their descriptions and optional tool lists.

**Parameters:**
- `include_tools` (boolean, optional) - Include tool lists for each context. Default: `false`

**Returns:**
- `contexts` (object) - All available contexts with descriptions and tool counts
- `total_contexts` (integer) - Number of available contexts
- `active_context` (string) - Currently active context

**Example:**
```json
{
  "include_tools": true
}
```

**Result:**
```json
{
  "contexts": {
    "baseline": {
      "description": "Minimal CRUD operations for basic database interaction",
      "tool_count": 7,
      "tools": ["arango_query", "arango_list_collections", ...]
    },
    "data_analysis": {
      "description": "Query optimization and performance analysis",
      "tool_count": 7,
      "tools": ["arango_query", "arango_explain_query", ...]
    },
    "graph_modeling": {
      "description": "Graph creation, traversal, and analysis",
      "tool_count": 10,
      "tools": ["arango_create_graph", "arango_traverse", ...]
    }
  },
  "total_contexts": 6,
  "active_context": "baseline"
}
```

### Workflow Example

**Scenario:** Multi-stage data pipeline with context switching

**Stage 1: Data Loading (baseline context)**
```
Agent: "Starting data import workflow. Switch to baseline context."

Call: arango_switch_context
Args: {"context": "baseline"}

Result: Switched to baseline (7 tools: query, insert, update, remove, list_collections, create_collection, backup)

Agent: "Load customer data from CSV."
Uses: arango_bulk_insert
Result: Inserted 10,000 customer records
```

**Stage 2: Data Analysis (data_analysis context)**
```
Agent: "Data loaded. Switch to data_analysis context for query optimization."

Call: arango_switch_context
Args: {"context": "data_analysis"}

Result: Switched to data_analysis (7 tools: query, explain_query, query_builder, query_profile, create_index, list_indexes, delete_index)

Agent: "Analyze query performance for customer lookups."
Uses: arango_explain_query, arango_create_index
Result: Created index on customers.email (95% query speedup)
```

**Stage 3: Graph Modeling (graph_modeling context)**
```
Agent: "Build customer relationship graph."

Call: arango_switch_context
Args: {"context": "graph_modeling"}

Result: Switched to graph_modeling (10 tools: create_graph, add_edge, traverse, shortest_path, graph_statistics, etc.)

Agent: "Create customer_relationships graph and analyze connections."
Uses: arango_create_graph, arango_add_edge, arango_graph_statistics
Result: Graph created with 10,000 vertices, 45,000 edges. Average degree: 4.5
```

**Token Savings:** By maintaining focused tool sets (7-10 tools per stage), the agent avoids loading all 43 tools throughout the workflow.

### Best Practices

**Match Context to Workflow Stage:**
- Use `baseline` for initial data loading and basic CRUD
- Switch to `data_analysis` for query optimization and indexing
- Use `graph_modeling` for relationship analysis
- Switch to `bulk_operations` for batch processing
- Use `schema_validation` for data integrity checks

**Minimize Context Switches:**
- Plan workflow stages to minimize context switching overhead
- Group related operations within the same context
- Use `full` context only when truly needed (complex multi-domain workflows)

**Verify Context Before Operations:**
- Call `arango_get_active_context` to confirm current tool set
- Ensure required tools are available before executing operations
- Switch contexts proactively rather than reactively

**Document Context Choices:**
- Explain why you chose a specific context
- Help users understand the workflow structure
- Make context switches explicit in logs and documentation

---

## Pattern 3: Tool Unloading

**Intent:** Explicitly remove tool definitions from the active context as workflows progress through stages, reducing cognitive load and context window consumption.

### How It Works

Tool Unloading allows AI agents to:
- Progress through predefined workflow stages (setup → data_loading → analysis → cleanup)
- Automatically unload tools from previous stages
- Manually unload specific tools no longer needed
- Track tool usage statistics to identify unused tools
- Maintain minimal, focused tool sets throughout workflow lifecycle

### Available Workflow Stages

The server provides 4 predefined workflow stages:

| Stage | Tools | Use Case |
|-------|-------|----------|
| **setup** | 8 | Database initialization, collection creation, schema setup |
| **data_loading** | 6 | Bulk data import, validation, initial indexing |
| **analysis** | 12 | Query execution, graph traversal, statistics generation |
| **cleanup** | 5 | Backup, validation, integrity checks, finalization |

### Available Tools

#### arango_advance_workflow_stage

Advance to the next workflow stage, automatically unloading tools from previous stage and loading tools for new stage.

**Parameters:**
- `stage` (string, required) - Workflow stage to advance to: `setup`, `data_loading`, `analysis`, `cleanup`

**Returns:**
- `from_stage` (string or null) - Previous stage (null if first stage)
- `to_stage` (string) - New active stage
- `description` (string) - Description of new stage
- `tools_added` (array) - Tools added in new stage
- `tools_removed` (array) - Tools removed from previous stage
- `total_active_tools` (integer) - Total tools in new stage
- `active_tools` (array) - All tools in new stage

**Example:**
```json
{
  "stage": "data_loading"
}
```

**Result:**
```json
{
  "from_stage": "setup",
  "to_stage": "data_loading",
  "description": "Bulk data import, validation, initial indexing",
  "tools_added": [
    "arango_bulk_insert",
    "arango_bulk_update",
    "arango_insert_with_validation"
  ],
  "tools_removed": [
    "arango_create_collection",
    "arango_create_schema"
  ],
  "total_active_tools": 6,
  "active_tools": [
    "arango_bulk_insert",
    "arango_bulk_update",
    "arango_insert_with_validation",
    "arango_validate_references",
    "arango_create_index",
    "arango_list_indexes"
  ]
}
```

#### arango_get_tool_usage_stats

Get usage statistics for all tools, including use counts and last used timestamps.

**Parameters:**
- None (empty object or omitted)

**Returns:**
- `total_tools` (integer) - Total number of tools
- `tools_used` (integer) - Number of tools that have been used
- `tools_unused` (integer) - Number of tools never used
- `usage_stats` (array) - Per-tool statistics with name, use_count, last_used, category

**Example:**
```json
{}
```

**Result:**
```json
{
  "total_tools": 43,
  "tools_used": 12,
  "tools_unused": 31,
  "usage_stats": [
    {
      "name": "arango_query",
      "use_count": 45,
      "last_used": "2025-11-11T10:30:15Z",
      "category": "core_data"
    },
    {
      "name": "arango_create_graph",
      "use_count": 3,
      "last_used": "2025-11-11T09:15:42Z",
      "category": "graph_basic"
    },
    {
      "name": "arango_backup",
      "use_count": 0,
      "last_used": null,
      "category": "core_data"
    }
  ]
}
```

**Use Cases:**
- Identify unused tools to unload
- Analyze tool usage patterns for optimization
- Debug workflow issues by tracking tool invocations
- Generate usage reports for team visibility

#### arango_unload_tools

Manually unload specific tools from the active context.

**Parameters:**
- `tool_names` (array of strings, required) - List of tool names to unload from active context

**Returns:**
- `unloaded_tools` (array) - Tools successfully unloaded
- `not_found` (array) - Tools not found in active context
- `remaining_tools` (integer) - Number of tools still active
- `active_tools` (array) - All remaining active tools

**Example:**
```json
{
  "tool_names": ["arango_backup", "arango_create_schema", "arango_validate_document"]
}
```

**Result:**
```json
{
  "unloaded_tools": [
    "arango_backup",
    "arango_create_schema"
  ],
  "not_found": [
    "arango_validate_document"
  ],
  "remaining_tools": 8,
  "active_tools": [
    "arango_query",
    "arango_insert",
    "arango_update",
    "arango_remove",
    "arango_list_collections",
    "arango_create_collection",
    "arango_bulk_insert",
    "arango_bulk_update"
  ]
}
```

**Use Cases:**
- Remove tools after completing a specific task
- Clean up context before switching workflows
- Manually optimize tool set based on usage patterns
- Reduce cognitive load during complex operations

### Workflow Example

**Scenario:** Complete data pipeline with automatic tool unloading

**Stage 1: Setup**
```
Agent: "Initialize database for customer analytics project."

Call: arango_advance_workflow_stage
Args: {"stage": "setup"}

Result: Loaded 8 setup tools (create_collection, create_schema, create_index, etc.)

Agent: "Create collections and schemas."
Uses: arango_create_collection, arango_create_schema, arango_create_index
Result: Created customers, orders, products collections with schemas and indexes
```

**Stage 2: Data Loading**
```
Agent: "Setup complete. Advance to data loading stage."

Call: arango_advance_workflow_stage
Args: {"stage": "data_loading"}

Result: Unloaded 5 setup tools, loaded 6 data loading tools (bulk_insert, bulk_update, insert_with_validation, etc.)

Agent: "Import customer and order data."
Uses: arango_bulk_insert, arango_insert_with_validation
Result: Imported 50,000 customers, 200,000 orders with validation
```

**Stage 3: Analysis**
```
Agent: "Data loaded. Advance to analysis stage."

Call: arango_advance_workflow_stage
Args: {"stage": "analysis"}

Result: Unloaded 4 data loading tools, loaded 12 analysis tools (query, traverse, graph_statistics, etc.)

Agent: "Analyze customer purchase patterns and relationships."
Uses: arango_query, arango_create_graph, arango_traverse, arango_graph_statistics
Result: Identified top 100 customers, 15 customer segments, 3 circular purchase patterns
```

**Stage 4: Cleanup**
```
Agent: "Analysis complete. Advance to cleanup stage."

Call: arango_advance_workflow_stage
Args: {"stage": "cleanup"}

Result: Unloaded 9 analysis tools, loaded 5 cleanup tools (backup, validate_graph_integrity, validate_references, etc.)

Agent: "Backup data and validate integrity."
Uses: arango_backup, arango_validate_graph_integrity
Result: Backup created (250MB), graph integrity validated (0 orphaned edges)
```

**Token Savings:** By unloading tools after each stage, the agent maintains 5-12 tools per stage instead of all 43 tools throughout the workflow.

### Best Practices

**Use Workflow Stages for Structured Pipelines:**
- Define clear stage boundaries (setup → data_loading → analysis → cleanup)
- Advance stages when transitioning between major workflow phases
- Let the server automatically manage tool loading/unloading

**Monitor Tool Usage:**
- Call `arango_get_tool_usage_stats` periodically to identify unused tools
- Unload tools with zero usage after initial workflow setup
- Track usage patterns to optimize future workflows

**Manual Unloading for Fine-Grained Control:**
- Use `arango_unload_tools` when workflow stages don't match your needs
- Unload tools immediately after completing a specific task
- Combine with Progressive Tool Discovery for maximum flexibility

**Balance Unloading with Reloading Costs:**
- Don't unload tools you'll need again soon
- Consider the cost of reloading tool definitions
- Use workflow stages for predictable patterns, manual unloading for dynamic workflows

---

## Combining Patterns

The three MCP design patterns work best when combined strategically based on workflow complexity and tool requirements.

### Hybrid Approach

**Scenario:** Complex multi-domain workflow requiring dynamic tool management

**Phase 1: Progressive Discovery + Context Switching**
```
1. Start with minimal context (baseline)
2. Search for graph tools → Load graph_modeling context
3. Search for validation tools → Manually add to context
4. Execute graph analysis workflow
```

**Phase 2: Context Switching + Tool Unloading**
```
1. Switch to data_analysis context
2. Execute query optimization workflow
3. Unload unused indexing tools
4. Advance to cleanup stage
```

### Decision Matrix

| Workflow Type | Recommended Pattern(s) | Rationale |
|---------------|------------------------|-----------|
| **Simple CRUD** | Context Switching (baseline) | Predefined tool set matches needs |
| **Exploratory Analysis** | Progressive Discovery | Unknown tool requirements upfront |
| **Multi-Stage Pipeline** | Tool Unloading (workflow stages) | Clear stage boundaries, predictable tool needs |
| **Complex Multi-Domain** | All Three Patterns | Dynamic requirements, multiple workflow phases |
| **Repetitive Tasks** | Context Switching | Consistent tool set across iterations |
| **One-Off Operations** | Progressive Discovery | Minimal setup, load only what's needed |

### Example: Complete Workflow

**Scenario:** Build and analyze a codebase dependency graph with full pattern integration

```
# Phase 1: Discovery (Progressive Tool Discovery)
Agent: "Search for graph and dependency tools."
Call: arango_search_tools(keywords=["graph", "dependency"])
Result: Found 12 tools

# Phase 2: Context Setup (Context Switching)
Agent: "Switch to graph_modeling context for focused tool set."
Call: arango_switch_context(context="graph_modeling")
Result: Loaded 10 graph tools

# Phase 3: Setup Stage (Tool Unloading)
Agent: "Advance to setup stage for graph creation."
Call: arango_advance_workflow_stage(stage="setup")
Result: Loaded 8 setup tools

Agent: "Create graph structure."
Uses: arango_create_graph, arango_create_collection
Result: Created codebase_dependencies graph

# Phase 4: Data Loading Stage
Agent: "Advance to data_loading stage."
Call: arango_advance_workflow_stage(stage="data_loading")
Result: Unloaded setup tools, loaded data loading tools

Agent: "Import module relationships."
Uses: arango_bulk_insert, arango_add_edge
Result: Imported 500 modules, 2,000 dependencies

# Phase 5: Analysis Stage
Agent: "Advance to analysis stage."
Call: arango_advance_workflow_stage(stage="analysis")
Result: Unloaded data loading tools, loaded analysis tools

Agent: "Analyze dependency graph."
Uses: arango_traverse, arango_graph_statistics, arango_shortest_path
Result: Found 3 circular dependencies, average depth: 4.2

# Phase 6: Cleanup Stage
Agent: "Advance to cleanup stage."
Call: arango_advance_workflow_stage(stage="cleanup")
Result: Unloaded analysis tools, loaded cleanup tools

Agent: "Validate and backup."
Uses: arango_validate_graph_integrity, arango_backup_graph
Result: Validation passed, backup created

# Phase 7: Usage Analysis (Tool Unloading)
Agent: "Check tool usage statistics."
Call: arango_get_tool_usage_stats()
Result: Used 15/43 tools, 28 tools never loaded (65% reduction)
```

**Estimated Total Token Savings:** ~130,000 tokens (87% reduction) by combining all three patterns

---

## Best Practices

### General Guidelines

**Start Minimal, Expand as Needed:**
- Begin with the smallest tool set that might work
- Use Progressive Discovery to find additional tools
- Avoid loading tools "just in case"

**Match Patterns to Workflow Characteristics:**
- Structured pipelines → Tool Unloading (workflow stages)
- Exploratory tasks → Progressive Discovery
- Repetitive workflows → Context Switching
- Complex multi-domain → Combine all three

**Monitor and Optimize:**
- Track tool usage with `arango_get_tool_usage_stats`
- Identify unused tools and unload them
- Refine context definitions based on actual usage patterns

**Document Tool Choices:**
- Explain why you loaded specific tools
- Make context switches explicit
- Help users understand workflow structure

### Performance Optimization

**Reduce Context Window Consumption:**
- Load tools with `detail_level: "summary"` for initial discovery
- Use `detail_level: "full"` only when ready to execute
- Unload tools immediately after completing tasks

**Minimize Tool Reloading:**
- Cache tool definitions within a session
- Don't unload tools you'll need again soon
- Use workflow stages for predictable patterns

**Combine with Code Execution:**
- Present tools as code APIs (filesystem-based discovery)
- Filter and transform data in execution environment
- Return only summaries to the model

### Error Handling

**Verify Tool Availability:**
- Check active context before executing operations
- Handle "tool not found" errors gracefully
- Switch contexts or load tools as needed

**Validate Context Switches:**
- Confirm successful context switch before proceeding
- Verify expected tools are available
- Fall back to `full` context if needed

**Track Workflow State:**
- Maintain awareness of current stage/context
- Log context switches and tool loading/unloading
- Enable workflow replay and debugging

---

## Related Documentation

- [Tools Reference](./tools-reference.md) - Complete documentation for all 43 MCP tools
- [Quick Start Guide](../getting-started/quick-start.md) - Get started with mcp-arangodb-async
- [Configuration Guide](../configuration/README.md) - Configure the MCP server
- [Graph Operations Guide](./graph-operations.md) - Comprehensive graph modeling documentation
- [Anthropic: Code Execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp) - Official MCP design pattern guidance

---

**Next Steps:**
1. Review the [Tools Reference](./tools-reference.md) to understand all available tools
2. Experiment with Progressive Tool Discovery in your workflows
3. Define custom contexts for your specific use cases
4. Monitor tool usage and optimize your patterns


