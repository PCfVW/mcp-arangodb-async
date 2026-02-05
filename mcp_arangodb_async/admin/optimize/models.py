"""Pydantic models for arango_admin_optimize tool."""

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AdminOptimizeArgs(BaseModel):
    """Arguments for log-driven edge optimization."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": "Admin optimization operations for tag_edges from logs"
        },
    )

    action: Literal["run", "quality_check"] = Field(
        default="run",
        description="Admin optimize operation"
    )
    dry_run: Optional[bool] = Field(
        default=None,
        description="Compute only, do not update edges"
    )
    days: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Lookback window (days) for log analysis"
    )
    alpha: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Blending factor for behavior signal into edge weight"
    )
    half_life_days: Optional[float] = Field(
        default=None,
        gt=0.0,
        description="Half-life for behavior decay"
    )
    enable_on: Optional[int] = Field(
        default=None,
        ge=1,
        le=64,
        description="Edge weight threshold to keep enabled"
    )
    disable_below: Optional[int] = Field(
        default=None,
        ge=1,
        le=64,
        description="Edge weight threshold to disable edge"
    )
    include_all_sources: Optional[bool] = Field(
        default=None,
        description="Include all tag_edges sources (not only auto/auto-sync)"
    )
    top_k: Optional[int] = Field(
        default=None,
        ge=1,
        le=100,
        description="Top-N items for noise/unstable edge lists"
    )
    orphan_limit: Optional[int] = Field(
        default=None,
        ge=1,
        le=200,
        description="Maximum orphan tags to return"
    )
    min_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for quality_check noise detection"
    )
    low_weight_threshold: Optional[int] = Field(
        default=None,
        ge=1,
        le=64,
        description="Low weight threshold for quality_check noise detection"
    )
