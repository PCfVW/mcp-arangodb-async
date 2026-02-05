"""Pydantic models for unified arango_admin tool."""

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AdminArgs(BaseModel):
    """Arguments for unified admin operations."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": "Unified admin operations: aql/template/sync/optimize"
        },
    )

    action: Literal[
        "aql_query",
        "aql_explain",
        "aql_profile",
        "aql_build",
        "template_execute",
        "sync_run",
        "optimize_run",
        "quality_check",
    ] = Field(description="Admin operation to perform")

    # Shared optional payloads (validated in delegated handlers)
    query: Optional[str] = Field(default=None, description="AQL query string")
    bind_vars: Optional[Dict[str, Any]] = Field(default=None, description="AQL bind vars")
    name: Optional[str] = Field(default=None, description="Template name")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Template params")
