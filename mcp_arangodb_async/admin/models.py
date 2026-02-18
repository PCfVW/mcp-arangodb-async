"""Pydantic models for unified arango_admin tool."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AdminArgs(BaseModel):
    """Arguments for unified admin operations."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "description": "Unified admin operations: aql/template/sync/optimize",
            "examples": [
                {
                    "action": "aql_query",
                    "query": "FOR d IN notes FILTER d.weight >= 30 LIMIT 10 RETURN d"
                },
                {
                    "action": "template_execute",
                    "name": "search.quaternary",
                    "params": {"query": "tags rule"}
                },
                {
                    "action": "sync_run",
                    "dry_run": True
                },
                {
                    "action": "embedding_run",
                    "embedding_action": "generate",
                    "batch_size": 64
                }
            ]
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
        "embedding_run",
    ] = Field(description="Admin operation to perform")

    # Shared optional payloads (validated in delegated handlers)
    query: Optional[str] = Field(default=None, description="AQL query string")
    bind_vars: Optional[Dict[str, Any]] = Field(default=None, description="AQL bind vars")
    name: Optional[str] = Field(default=None, description="Template name")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Template params")

    # Embedding params (for embedding_run action)
    embedding_action: Optional[Literal["generate", "search", "status"]] = Field(
        default=None,
        description="Embedding sub-action: generate, search, or status. Default: status",
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Specific tag labels to generate embeddings for",
    )
    model_name: Optional[str] = Field(
        default=None,
        description="HuggingFace model name. Default: Qwen/Qwen3-Embedding-0.6B",
    )
    batch_size: Optional[int] = Field(
        default=None,
        description="Batch size for embedding generation. Default: 64",
    )
    top_k: Optional[int] = Field(
        default=None,
        description="Max similar tags per query token. Default: 5",
    )
    threshold: Optional[float] = Field(
        default=None,
        description="Minimum cosine similarity threshold. Default: 0.5",
    )
    limit: Optional[int] = Field(
        default=None,
        description="Max notes to return. Default: 20",
    )
