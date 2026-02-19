"""Pydantic models for MCP metadata operations (v4.0).

Purpose:
    Defines Pydantic v2 models for validating inputs to MCP metadata operations.
    Handles tool discovery, workflow management, and tool lifecycle.

Operations:
    - search_tools: Search tools by keywords and categories
    - list_by_category: List tools grouped by category
    - get_workflow: Get currently active workflow context
    - list_workflows: List available workflow contexts
    - usage_stats: Get tool usage statistics
    - unload: Unload tools from active context
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class MCPArgs(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: Literal[
        "search_tools",
        "list_by_category",
        "get_workflow",
        "list_workflows",
        "usage_stats",
        "unload"
    ] = Field(description="MCP metadata operation to perform")


# Tool Discovery Operations

class SearchToolsArgs(BaseModel):
    """Arguments for search_tools operation.

    Searches tools by keywords and optionally filters by categories.
    Pattern: Progressive Tool Discovery
    """

    model_config = ConfigDict(extra="allow")

    keywords: List[str] = Field(
        description="Keywords to search for in tool names and descriptions"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Filter by categories: core_data, indexing, validation, schema, query, graph_basic, graph_advanced, aliases, health"
    )
    detail_level: Literal["name", "summary", "full"] = Field(
        default="full",
        description="Level of detail: 'name' (just names), 'summary' (names + descriptions), 'full' (complete schemas with action params)"
    )


class ListByCategoryArgs(BaseModel):
    """Arguments for list_by_category operation.

    Lists tools grouped by category. If no category specified, returns all.
    """

    model_config = ConfigDict(extra="allow")

    category: Optional[str] = Field(
        default=None,
        description="Category to filter by (if None, returns all categories)"
    )


# Workflow Operations

class GetWorkflowArgs(BaseModel):
    """Arguments for get_workflow operation.

    Returns the currently active workflow context.
    No additional parameters required.
    """

    model_config = ConfigDict(extra="allow")


class ListWorkflowsArgs(BaseModel):
    """Arguments for list_workflows operation.

    Lists available workflow contexts and their tools.
    """

    model_config = ConfigDict(extra="allow")

    include_tools: bool = Field(
        default=False,
        description="Include tool lists for each context"
    )


# Usage Statistics Operations

class UsageStatsArgs(BaseModel):
    """Arguments for usage_stats operation.

    Gets tool usage statistics and metrics.
    No additional parameters required.
    """

    model_config = ConfigDict(extra="allow")


# Tool Lifecycle Operations

class UnloadArgs(BaseModel):
    """Arguments for unload operation.

    Unloads specified tools from the active context.
    """

    model_config = ConfigDict(extra="allow")

    tool_names: List[str] = Field(
        description="List of tool names to unload"
    )
