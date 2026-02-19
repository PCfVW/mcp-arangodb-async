"""Pydantic models for database operations (v4.0).

Purpose:
    Defines Pydantic v2 models for validating inputs to database operations.
    These models provide type checking and JSON schema generation for MCP tools.

Operations:
    - get_focused: Get currently focused database for the current session
    - list_available: List all configured databases
    - get_resolution: Show database resolution algorithm result
    - backup: Backup entire database or specific collections
    - restore: Restore database from backup directory
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class DatabaseArgs(BaseModel):
    model_config = ConfigDict(extra="allow")

    action: Literal["list", "get_focused", "switch", "get_resolution", "list_available", "backup", "restore"] = Field(
        description="Database operation to perform"
    )


class GetFocusedArgs(BaseModel):
    """Arguments for get_focused operation.

    Retrieves the currently focused database for the current session.
    No additional parameters required.
    """

    model_config = ConfigDict(extra="allow")


class ListAvailableArgs(BaseModel):
    """Arguments for list_available operation.

    Lists all configured databases from the configuration.
    No additional parameters required.
    """

    model_config = ConfigDict(extra="allow")


class SwitchArgs(BaseModel):
    """Arguments for switch operation.

    Sets the focused database for the current session.
    Pass None or empty string to unset the focused database.
    """

    model_config = ConfigDict(extra="allow")

    database: Optional[str] = Field(
        default=None,
        description="Database key to switch to. Pass None or empty string to unset."
    )


class GetResolutionArgs(BaseModel):
    """Arguments for get_resolution operation.

    Shows the database resolution algorithm and which level was used.
    Displays the 6-level priority fallback mechanism:
    1. Per-tool override
    2. Focused database
    3. Config default
    4. Environment variable
    5. First configured database
    6. Hardcoded fallback (_system)

    No additional parameters required.
    """

    model_config = ConfigDict(extra="allow")
