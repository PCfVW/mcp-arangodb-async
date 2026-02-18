"""Runtime defaults loader for config-driven parameters.

Loads local JSON config files (DB-agnostic control plane defaults).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
ADMIN_CONFIG_PATH = CONFIG_DIR / "admin.json"
TOOLS_CONFIG_PATH = CONFIG_DIR / "tools.json"
HELP_CONFIG_PATH = CONFIG_DIR / "help.json"

_admin_cache: Dict[str, Any] | None = None
_tools_cache: Dict[str, Any] | None = None
_help_cache: Dict[str, Any] | None = None


def _load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            logger.warning("Config file is not object: %s", path)
            return default
    except FileNotFoundError:
        return default
    except Exception as exc:
        logger.warning("Failed loading config %s: %s", path, exc)
        return default


def get_admin_defaults(section: str) -> Dict[str, Any]:
    """Get admin defaults for a given section (sync/optimize)."""
    global _admin_cache
    if _admin_cache is None:
        _admin_cache = _load_json(ADMIN_CONFIG_PATH, {})

    defaults = _admin_cache.get(section, {})
    if isinstance(defaults, dict):
        return defaults
    return {}


def get_tools_metadata() -> Dict[str, Any]:
    """Get tools metadata loaded from config/tools.json."""
    global _tools_cache
    if _tools_cache is None:
        _tools_cache = _load_json(TOOLS_CONFIG_PATH, {"tools": []})
    return _tools_cache


def get_help_metadata() -> Dict[str, Any]:
    """Get help documentation loaded from config/help.json."""
    global _help_cache
    if _help_cache is None:
        _help_cache = _load_json(HELP_CONFIG_PATH, {"tools": {}})
    return _help_cache


def get_available_actions(tool_name: str) -> list[str]:
    """Get available actions for a tool from tools.json.

    Args:
        tool_name: Tool name (e.g., "arango_collection")

    Returns:
        List of action names, empty if tool not found
    """
    tools_meta = get_tools_metadata()
    for tool in tools_meta.get("tools", []):
        if tool.get("name") == tool_name:
            return tool.get("actions", [])
    return []


def get_action_help(tool_name: str, action: str) -> Dict[str, Any] | None:
    """Get help for a specific action from help.json.

    Args:
        tool_name: Tool name (e.g., "arango_collection")
        action: Action name (e.g., "insert")

    Returns:
        Action help dict (params, example, description) or None
    """
    help_meta = get_help_metadata()
    tool_help = help_meta.get("tools", {}).get(tool_name, {})
    actions = tool_help.get("actions", {})
    return actions.get(action)
