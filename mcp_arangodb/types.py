"""
ArangoDB MCP Server - TypedDict Type Definitions

This module defines TypedDict classes for type hints and validation.
Kept for potential future use alongside Pydantic models in models.py.

Classes:
- QueryArgs - TypedDict for AQL query arguments
- ListCollectionsArgs - TypedDict for collection listing arguments (empty)
- InsertArgs - TypedDict for document insertion arguments
- UpdateArgs - TypedDict for document update arguments
- RemoveArgs - TypedDict for document removal arguments
- CreateCollectionArgs - TypedDict for collection creation arguments
- BackupArgs - TypedDict for backup operation arguments
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict


class QueryArgs(TypedDict, total=True):
    query: str
    bind_vars: Optional[Dict[str, Any]]


class ListCollectionsArgs(TypedDict, total=False):
    # no args
    pass


class InsertArgs(TypedDict, total=True):
    collection: str
    document: Dict[str, Any]


class UpdateArgs(TypedDict, total=True):
    collection: str
    key: str
    update: Dict[str, Any]


class RemoveArgs(TypedDict, total=True):
    collection: str
    key: str


class CreateCollectionArgs(TypedDict, total=False):
    name: str
    type: str  # "document" | "edge"
    waitForSync: Optional[bool]


class BackupArgs(TypedDict, total=False):
    output_dir: Optional[str]
    collections: Optional[List[str]]
    doc_limit: Optional[int]
