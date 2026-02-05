"""Pydantic models for view operations (v4.0).

Purpose:
    Defines Pydantic v2 models for validating inputs to ArangoSearch view operations.
    Covers view creation, configuration, and search execution.

Operations:
    Management:
    - create: Create an ArangoSearch view
    - drop: Drop a view
    - list: List all views
    - get: Get view properties
    - update: Update view properties

    Search:
    - search: Execute search query against view
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class ViewArgs(BaseModel):
    """Base model for view operations with action-based dispatch."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": "View tool arguments with action-based dispatch"
        }
    )

    action: Literal[
        # Management
        "create", "drop", "list", "get", "update",
        # Search
        "search"
    ] = Field(description="View operation to perform")


# Management Operations

class CreateViewArgs(BaseModel):
    """Arguments for create operation (create view)."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Name of the view")
    type: Literal["arangosearch"] = Field(
        default="arangosearch",
        description="Type of view (currently only arangosearch)"
    )
    properties: Optional[Dict[str, Any]] = Field(
        default=None,
        description="View properties including links, analyzers, etc."
    )
    database: Optional[str] = Field(default=None, description="Database override")


class DropViewArgs(BaseModel):
    """Arguments for drop operation (drop view)."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Name of the view to drop")
    database: Optional[str] = Field(default=None, description="Database override")


class ListViewsArgs(BaseModel):
    """Arguments for list operation (list views)."""

    model_config = ConfigDict(extra="allow")

    database: Optional[str] = Field(default=None, description="Database override")


class GetViewArgs(BaseModel):
    """Arguments for get operation (get view properties)."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Name of the view")
    database: Optional[str] = Field(default=None, description="Database override")


class UpdateViewArgs(BaseModel):
    """Arguments for update operation (update view properties)."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Name of the view")
    properties: Dict[str, Any] = Field(
        description="View properties to update (links, analyzers, etc.)"
    )
    database: Optional[str] = Field(default=None, description="Database override")


# Search Operations

class SearchViewArgs(BaseModel):
    """Arguments for search operation (execute search query)."""

    model_config = ConfigDict(extra="allow")

    name: str = Field(description="Name of the view")
    query: str = Field(description="AQL query string to execute against the view")
    bind_vars: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Bind variables for the query"
    )
    database: Optional[str] = Field(default=None, description="Database override")
