"""Pydantic models for unified arango_admin tool."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AdminArgs(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: Literal[
        "aql_query",
        "aql_explain",
        "aql_profile",
        "aql_build",
        "template_execute",
        "sync_run",
        "optimize_run",
        "quality_check",
        "embedding_run",
    ] = Field(description="Admin operation to perform")
