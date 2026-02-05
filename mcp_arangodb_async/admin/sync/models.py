"""Pydantic models for arango_admin_sync tool."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AdminSyncArgs(BaseModel):
    """Arguments for tag/tag_edge synchronization."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": "Admin sync operations for tags and tag_edges"
        },
    )

    action: Literal["run"] = Field(
        default="run",
        description="Admin sync operation"
    )
    dry_run: Optional[bool] = Field(
        default=None,
        description="Compute only, do not write to database"
    )
    min_cooccur_count: Optional[int] = Field(
        default=None,
        ge=1,
        description="Minimum co-occurrence count to create AND/OR edges"
    )
    and_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Conditional probability threshold for AND edges"
    )
    or_threshold: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Conditional probability threshold for OR edges"
    )
    min_tag_count_for_not: Optional[int] = Field(
        default=None,
        ge=1,
        description="Minimum tag frequency for NOT/XOR candidate pool"
    )
    max_not_tags: Optional[int] = Field(
        default=None,
        ge=10,
        le=1000,
        description="Max frequent tags used to derive NOT/XOR edges"
    )
    xor_shared_min: Optional[int] = Field(
        default=None,
        ge=1,
        description="Shared neighbor count threshold for XOR derivation"
    )
    clear_previous_auto: Optional[bool] = Field(
        default=None,
        description="Remove prior auto-generated edges before write"
    )
