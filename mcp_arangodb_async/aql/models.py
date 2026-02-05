"""Pydantic models for AQL operations (v4.0).

Purpose:
    Defines Pydantic v2 models for validating inputs to AQL operations.
    Covers query execution, query analysis, profiling, and query building.

Operations:
    Query:
    - query: Execute an AQL query
    - explain: Explain query execution plan
    - profile: Profile query execution

    Builder:
    - build: Build a query from filters and sort
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class AQLArgs(BaseModel):
    """Base model for AQL operations with action-based dispatch."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": "AQL tool arguments with action-based dispatch"
        }
    )

    action: Literal[
        # Query
        "query", "explain", "profile",
        # Builder
        "build"
    ] = Field(description="AQL operation to perform")


# Query Operations

class QueryArgs(BaseModel):
    """Arguments for query operation (execute AQL query)."""

    model_config = ConfigDict(extra="allow")

    query: str = Field(description="AQL query string")
    bind_vars: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Bind variables for the query"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class ExplainArgs(BaseModel):
    """Arguments for explain operation (explain query plan)."""

    model_config = ConfigDict(extra="allow")

    query: str = Field(description="AQL query string")
    bind_vars: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Bind variables for the query"
    )
    suggest_indexes: bool = Field(
        default=True,
        description="Suggest indexes for optimization"
    )
    max_plans: int = Field(
        default=1,
        ge=1,
        description="Maximum number of plans to return"
    )
    database: Optional[str] = Field(default=None, description="Database override")


class ProfileArgs(BaseModel):
    """Arguments for profile operation (profile query execution)."""

    model_config = ConfigDict(extra="allow")

    query: str = Field(description="AQL query string")
    bind_vars: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Bind variables for the query"
    )
    max_plans: int = Field(
        default=1,
        ge=1,
        description="Maximum number of plans to profile"
    )
    database: Optional[str] = Field(default=None, description="Database override")


# Query Builder Operations

class QueryFilter(BaseModel):
    """Filter specification for query builder."""

    field: str = Field(description="Field name to filter")
    op: Literal["==", "!=", "<", "<=", ">", ">=", "IN", "LIKE"] = Field(
        description="Filter operator"
    )
    value: Any = Field(description="Filter value")


class QuerySort(BaseModel):
    """Sort specification for query builder."""

    field: str = Field(description="Field name to sort by")
    direction: Literal["ASC", "DESC"] = Field(
        default="ASC",
        description="Sort direction"
    )


class BuildArgs(BaseModel):
    """Arguments for build operation (query builder)."""

    model_config = ConfigDict(extra="allow")

    collection: str = Field(description="Collection to query")
    filters: List[QueryFilter] = Field(
        default_factory=list,
        description="Filter specifications"
    )
    sort: List[QuerySort] = Field(
        default_factory=list,
        description="Sort specifications"
    )
    limit: Optional[int] = Field(
        default=None,
        ge=0,
        description="Result limit"
    )
    return_fields: Optional[List[str]] = Field(
        default=None,
        description="Fields to project in results"
    )
    database: Optional[str] = Field(default=None, description="Database override")
