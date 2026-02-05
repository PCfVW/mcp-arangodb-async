"""Template operation models."""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class TemplateArgs(BaseModel):
    """Arguments for template operations.

    Template operations execute pre-built or custom query templates
    with parameter validation and default values.

    Operations:
    - execute: Execute a template by name with parameters
    - list: List available templates (optional: by category)

    Example:
        {"name": "memory.recent", "params": {"limit": 10}}
        {"name": "heap.top", "params": {"limit": 5}}
    """

    name: str = Field(
        description="Template name (e.g., 'memory.recent', 'heap.top')"
    )

    params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Template parameters (validated against template schema)"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "name": "memory.recent",
                    "params": {"limit": 10}
                },
                {
                    "name": "heap.by_layer",
                    "params": {"layer": 1}
                },
                {
                    "name": "graph.related",
                    "params": {"start_id": "notes/123", "depth": 2}
                }
            ]
        }
