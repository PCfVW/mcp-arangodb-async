"""Database resolution algorithm for multi-tenancy support.

This module provides deterministic database selection using a 6-level priority
fallback mechanism, enabling both focused database context and per-tool overrides.
"""

import os
from typing import Any, Dict, Optional
from .session import SessionState
from .config_loader import ConfigFileLoader


def resolve_database(
    tool_args: Dict[str, Any],
    session_state: SessionState,
    session_id: str,
    config_loader: ConfigFileLoader
) -> str:
    """Resolve database using 6-level priority fallback.
    
    Priority levels (in order):
    1. Per-tool override (tool_args["database"])
    2. Focused database (session_state.get_focused_database())
    3. Config default (config_loader.default_database)
    4. Environment variable (ARANGO_DB)
    5. First configured database
    6. Hardcoded fallback ("_system")
    
    Args:
        tool_args: Tool arguments dictionary (may contain "database" key)
        session_state: SessionState instance for session-scoped state
        session_id: Unique session identifier
        config_loader: ConfigFileLoader instance with database configurations
        
    Returns:
        Database key to use for this tool call
    """
    # Level 1: Per-tool override (does NOT mutate session state)
    if "database" in tool_args and tool_args["database"]:
        return tool_args["database"]
    
    # Level 2: Focused database (session-scoped)
    focused = session_state.get_focused_database(session_id)
    if focused:
        return focused
    
    # Level 3: Config default
    if config_loader.default_database:
        return config_loader.default_database
    
    # Level 4: Environment variable
    env_default = os.getenv("ARANGO_DB")
    if env_default:
        return env_default
    
    # Level 5: First configured database
    databases = config_loader.get_configured_databases()
    if databases:
        return list(databases.keys())[0]
    
    # Level 6: Hardcoded fallback
    return "_system"

