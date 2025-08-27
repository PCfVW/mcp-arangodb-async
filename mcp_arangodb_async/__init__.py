"""
ArangoDB MCP Server - Package Initialization

This module defines the public API for the mcp_arangodb_async package.
Exports core configuration and database connection utilities.

Exported Functions:
- load_config() - Load configuration from environment variables
- get_client_and_db() - Create ArangoDB client and database connection

Exported Classes:
- Config - Configuration dataclass
"""

__all__ = [
    "Config",
    "load_config",
    "get_client_and_db",
]

from .config import Config, load_config
from .db import get_client_and_db
