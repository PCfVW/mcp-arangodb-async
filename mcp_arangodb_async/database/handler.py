"""
Database Operations Handler

Purpose:
    Implements handler functions for database-level operations.
    These operations handle multi-tenancy features, database resolution,
    and database management across the MCP server.

Operations (v4.0):
    - list: List all configured databases
    - get_focused: Get currently focused database for the current session
    - switch: Set focused database for the current session
    - get_resolution: Show database resolution algorithm result for current session
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import logging
from arango.database import StandardDatabase

from .backup import backup_database, restore_database
from ..utility.runtime_defaults import get_available_actions

logger = logging.getLogger(__name__)


def handle_errors(func):
    """Decorator to standardize error handling across handlers."""
    import asyncio
    from functools import wraps

    # Common error handling logic
    def handle_exception(e: Exception, func_name: str) -> Dict[str, Any]:
        if isinstance(e, KeyError):
            logger.error(f"Missing required parameter in {func_name}: {e}")
            return {
                "error": f"Missing required parameter: {str(e)}",
                "action": func_name,
            }
        else:
            logger.exception(f"Unexpected error in {func_name}")
            return {"error": f"Operation failed: {str(e)}", "action": func_name}

    # Check if the function is async
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(
            db: StandardDatabase, args: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            try:
                if args is None:
                    return await func(db)
                else:
                    return await func(db, args)
            except Exception as e:
                return handle_exception(e, func.__name__)

        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(
            db: StandardDatabase, args: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            try:
                if args is None:
                    return func(db)
                else:
                    return func(db, args)
            except Exception as e:
                return handle_exception(e, func.__name__)

        return sync_wrapper


@handle_errors
def get_focused(
    db: StandardDatabase, args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Get currently focused database for the current session.

    Args:
        db: ArangoDB database instance (not used, but required for handler signature)
        args: Optional arguments (may contain session context)

    Returns:
        Dictionary with focused database information
    """
    # Extract session context
    if args is None:
        args = {}
    session_ctx = args.pop("_session_context", {})
    session_state = session_ctx.get("session_state")
    session_id = session_ctx.get("session_id", "stdio")

    if session_state:
        focused_db = session_state.get_focused_database(session_id)
        return {
            "focused_database": focused_db,
            "session_id": session_id,
            "is_set": focused_db is not None
        }
    else:
        return {
            "focused_database": None,
            "session_id": session_id,
            "is_set": False,
            "error": "Session state not available"
        }


@handle_errors
def list_databases(
    db: StandardDatabase, args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """List all configured databases.

    Args:
        db: ArangoDB database instance (not used, but required for handler signature)
        args: Optional arguments (may contain session context)

    Returns:
        Dictionary with list of available databases
    """
    # Extract session context
    if args is None:
        args = {}
    session_ctx = args.pop("_session_context", {})
    db_manager = session_ctx.get("db_manager")

    if db_manager:
        configured_dbs = db_manager.get_configured_databases()
        databases = []
        for db_key, db_config in configured_dbs.items():
            databases.append({
                "key": db_key,
                "url": db_config.url,
                "database": db_config.database,
                "username": db_config.username
            })

        return {
            "databases": databases,
            "total_count": len(databases)
        }
    else:
        return {
            "databases": [],
            "total_count": 0,
            "error": "Database manager not available"
        }


@handle_errors
def get_resolution(
    db: StandardDatabase, args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Show database resolution for current session.

    Uses the centralized resolve_database() function to ensure consistency
    with actual database resolution logic, then builds diagnostic information
    around the resolved result.

    Displays the 6-level priority fallback mechanism:
    1. Per-tool override (tool_args["database"])
    2. Focused database (session_state.get_focused_database())
    3. Config default (config_loader.default_database)
    4. Environment variable (ARANGO_DB)
    5. First configured database
    6. Hardcoded fallback ("_system")

    Args:
        db: ArangoDB database instance (not used, but required for handler signature)
        args: Optional arguments (may contain session context)

    Returns:
        Dictionary with database resolution details
    """
    import os
    from ..utility.resolver import resolve_database

    # Extract session context
    if args is None:
        args = {}
    session_ctx = args.pop("_session_context", {})
    session_state = session_ctx.get("session_state")
    session_id = session_ctx.get("session_id", "stdio")
    db_manager = session_ctx.get("db_manager")
    config_loader = session_ctx.get("config_loader")

    # Use centralized resolver for actual resolution (no tool override for diagnostic)
    resolved_db = None
    if session_state and config_loader:
        resolved_db = resolve_database(
            tool_args={},  # No tool override for diagnostic
            session_state=session_state,
            session_id=session_id,
            config_loader=config_loader
        )

    # Build diagnostic information around the resolved result
    resolution = {
        "session_id": session_id,
        "resolved_database": resolved_db,
        "levels": {}
    }

    # Level 1: Per-tool override (not applicable for this tool)
    resolution["levels"]["1_per_tool_override"] = {
        "value": None,
        "description": "Per-tool database parameter (not applicable for this query)"
    }

    # Level 2: Focused database
    focused_db = session_state.get_focused_database(session_id) if session_state else None
    resolution["levels"]["2_focused_database"] = {
        "value": focused_db,
        "description": "Session-scoped focused database"
    }

    # Level 3: Config default
    config_default = config_loader.default_database if config_loader else None
    resolution["levels"]["3_config_default"] = {
        "value": config_default,
        "description": "Default database from configuration file"
    }

    # Level 4: Environment variable
    env_default = os.getenv("ARANGO_DB")
    resolution["levels"]["4_env_variable"] = {
        "value": env_default,
        "description": "ARANGO_DB environment variable"
    }

    # Level 5: First configured database
    first_configured = None
    if db_manager:
        configured_dbs = db_manager.get_configured_databases()
        if configured_dbs:
            first_configured = list(configured_dbs.keys())[0]
    resolution["levels"]["5_first_configured"] = {
        "value": first_configured,
        "description": "First database in configuration"
    }

    # Level 6: Hardcoded fallback
    resolution["levels"]["6_hardcoded_fallback"] = {
        "value": "_system",
        "description": "Hardcoded fallback database"
    }

    # Determine which level was used by comparing with resolved result
    resolved_level = None
    for level_key in ["2_focused_database", "3_config_default", "4_env_variable", "5_first_configured", "6_hardcoded_fallback"]:
        if resolution["levels"][level_key]["value"] == resolved_db:
            resolved_level = level_key
            break

    resolution["resolved_level"] = resolved_level

    # Add comprehensive configuration information
    if config_loader:
        resolution["configuration"] = {
            "source": "yaml_file" if getattr(config_loader, "loaded_from_yaml", False) else "environment_variables",
            "config_path": getattr(config_loader, "config_path", None) if getattr(config_loader, "loaded_from_yaml", False) else None,
            "default_database": getattr(config_loader, "default_database", None),
            "total_databases": len(config_loader.get_configured_databases()),
            "database_keys": list(config_loader.get_configured_databases().keys())
        }

        # Add details for each configured database
        resolution["databases"] = {}
        for db_key, db_config in config_loader.get_configured_databases().items():
            resolution["databases"][db_key] = {
                "url": getattr(db_config, "url", None),
                "database": getattr(db_config, "database", None),
                "username": getattr(db_config, "username", None),
                "timeout": getattr(db_config, "timeout", None)
            }
    else:
        resolution["configuration"] = {
            "error": "config_loader not available"
        }

    return resolution


@handle_errors
def switch(
    db: StandardDatabase, args: Dict[str, Any]
) -> Dict[str, Any]:
    """Set focused database for the current session.

    This operation allows switching the focused database within a session.
    Useful for HTTP transport where sessions persist, or for complex
    multi-database operations within a single MCP request.

    Pass None or empty string to unset the focused database and revert to
    default database resolution.

    Args:
        db: ArangoDB database instance (not used, but required for handler signature)
        args: Arguments containing 'database' key (can be None to unset)

    Returns:
        Dictionary with success status and new focused database
    """
    # Extract session context
    session_ctx = args.pop("_session_context", {})
    session_state = session_ctx.get("session_state")
    session_id = session_ctx.get("session_id", "stdio")
    db_manager = session_ctx.get("db_manager")

    database_key = args.get("database")

    # Check if unsetting the focused database (None or empty string)
    if database_key is None or database_key == "":
        # Unset focused database in session state
        if session_state:
            session_state.set_focused_database_sync(session_id, None)

            # Determine which database will be used after unsetting
            from ..utility.resolver import resolve_database
            config_loader = session_ctx.get("config_loader")
            fallback_db = None
            if config_loader:
                fallback_db = resolve_database(
                    tool_args={},
                    session_state=session_state,
                    session_id=session_id,
                    config_loader=config_loader
                )

            message = "Focused database has been unset. Database resolution will fall back to default priority levels"
            if fallback_db:
                message += f" (will use '{fallback_db}')"

            return {
                "success": True,
                "focused_database": None,
                "session_id": session_id,
                "message": message,
                "fallback_database": fallback_db
            }
        else:
            return {
                "success": False,
                "error": "Session state not available"
            }

    # Validate database exists in configuration
    if db_manager:
        configured_dbs = db_manager.get_configured_databases()
        if database_key not in configured_dbs:
            return {
                "success": False,
                "error": f"Database '{database_key}' not configured",
                "available_databases": list(configured_dbs.keys())
            }

    # Set focused database in session state
    if session_state:
        session_state.set_focused_database_sync(session_id, database_key)
        return {
            "success": True,
            "focused_database": database_key,
            "session_id": session_id
        }
    else:
        return {
            "success": False,
            "error": "Session state not available"
        }


# OPERATIONS dispatch dictionary for v4.0 tool architecture
OPERATIONS = {
    "list": list_databases,
    "get_focused": get_focused,
    "switch": switch,
    "get_resolution": get_resolution,
    "backup": backup_database,
    "restore": restore_database,
    # Aliases for backward compatibility
    "list_available": list_databases,
}


def handle_database(db: StandardDatabase, action: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Main handler for database operations.

    Dispatches to appropriate operation handler based on action name.

    Args:
        db: ArangoDB database instance
        action: Operation action name (key in OPERATIONS dict)
        args: Optional arguments for the operation

    Returns:
        Result dictionary from the operation handler
    """
    if action not in OPERATIONS:
        available = get_available_actions("arango_database")
        return {
            "error": f"Unknown action: {action}",
            "tool": "arango_database",
            "available_actions": available,
            "hint": f"Use one of: {', '.join(available)}"
        }

    handler = OPERATIONS[action]
    return handler(db, args)
