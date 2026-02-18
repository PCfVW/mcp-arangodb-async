"""MCP metadata operations driven by local JSON schemas.

This module intentionally avoids DB-dependent metadata and avoids hard-coded
legacy tool registries. Tool discovery/help/workflow definitions are loaded
from config/*.json so the control plane remains available even when DB is down.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from arango.database import StandardDatabase

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
TOOLS_CONFIG_PATH = CONFIG_DIR / "tools.json"
HELP_CONFIG_PATH = CONFIG_DIR / "help.json"
WORKFLOWS_CONFIG_PATH = CONFIG_DIR / "workflows.json"

_tools_cache: Optional[Dict[str, Dict[str, Any]]] = None
_help_cache: Optional[Dict[str, Dict[str, Any]]] = None
_workflow_cache: Optional[Dict[str, Any]] = None


def _load_json(path: Path, default: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Metadata config missing: %s", path)
    except Exception as exc:
        logger.warning("Metadata config parse failed: %s (%s)", path, exc)
    return default


def _load_tools() -> Dict[str, Dict[str, Any]]:
    global _tools_cache
    if _tools_cache is not None:
        return _tools_cache

    raw = _load_json(TOOLS_CONFIG_PATH, {"tools": []})
    tools = raw.get("tools", [])

    mapping: Dict[str, Dict[str, Any]] = {}
    if isinstance(tools, list):
        for item in tools:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if isinstance(name, str) and name:
                mapping[name] = item
    elif isinstance(tools, dict):
        for name, item in tools.items():
            if isinstance(name, str) and isinstance(item, dict):
                merged = dict(item)
                merged.setdefault("name", name)
                mapping[name] = merged

    _tools_cache = mapping
    return mapping


def _load_help() -> Dict[str, Dict[str, Any]]:
    global _help_cache
    if _help_cache is not None:
        return _help_cache

    raw = _load_json(HELP_CONFIG_PATH, {"tools": {}})
    tools = raw.get("tools", {})
    _help_cache = tools if isinstance(tools, dict) else {}
    return _help_cache


def _default_workflows(tool_names: List[str]) -> Dict[str, Any]:
    baseline = tool_names[: min(7, len(tool_names))]
    return {
        "contexts": {
            "baseline": {
                "description": "Baseline context with core tools",
                "tools": baseline,
            },
            "full": {
                "description": "All configured tools",
                "tools": tool_names,
            },
        },
        "stages": {
            "setup": {
                "description": "Initialization stage",
                "tools": baseline,
            },
            "analysis": {
                "description": "Analysis stage",
                "tools": tool_names,
            },
            "cleanup": {
                "description": "Finalize stage",
                "tools": tool_names,
            },
        },
    }


def _load_workflows() -> Dict[str, Any]:
    global _workflow_cache
    if _workflow_cache is not None:
        return _workflow_cache

    tools = _load_tools()
    fallback = _default_workflows(list(tools.keys()))
    raw = _load_json(WORKFLOWS_CONFIG_PATH, fallback)

    contexts = raw.get("contexts", {}) if isinstance(raw, dict) else {}
    stages = raw.get("stages", {}) if isinstance(raw, dict) else {}

    if not contexts:
        contexts = fallback["contexts"]
    if not stages:
        stages = fallback["stages"]

    _workflow_cache = {"contexts": contexts, "stages": stages}
    return _workflow_cache


def _infer_category(name: str, tool: Dict[str, Any]) -> str:
    if isinstance(tool.get("category"), str) and tool["category"]:
        return tool["category"]

    lower = name.lower()
    if "graph" in lower:
        return "graph"
    if "aql" in lower or "query" in lower:
        return "query"
    if "template" in lower:
        return "template"
    if "admin" in lower:
        return "admin"
    if "mcp" in lower:
        return "mcp"
    if "collection" in lower:
        return "collection"
    if "database" in lower:
        return "database"
    if "view" in lower:
        return "view"
    return "core"


def _get_tool_categories() -> Dict[str, List[str]]:
    tools = _load_tools()
    categories: Dict[str, List[str]] = {}

    for name, tool in tools.items():
        cat = _infer_category(name, tool)
        categories.setdefault(cat, []).append(name)

    for cat in categories:
        categories[cat].sort()

    return categories


def _tool_summary(name: str, detail_level: str) -> Dict[str, Any]:
    tools = _load_tools()
    help_tools = _load_help()
    tool = tools.get(name, {"name": name})
    help_item = help_tools.get(name, {})

    if detail_level == "name":
        return {"name": name}

    summary = {
        "name": name,
        "description": tool.get("description")
        or help_item.get("description")
        or "",
    }

    if detail_level == "full":
        if "usage" in tool:
            summary["usage"] = tool["usage"]
        if "operations" in help_item:
            summary["operations"] = help_item["operations"]
        if "actions" in help_item:
            summary["actions"] = help_item["actions"]
        if "parameters" in help_item:
            summary["parameters"] = help_item["parameters"]

    return summary


def _get_session_context(args: Dict[str, Any]) -> tuple:
    session_ctx = args.pop("_session_context", {})
    session_state = session_ctx.get("session_state")
    session_id = session_ctx.get("session_id", "stdio")
    return session_state, session_id


def search_tools(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    keywords = [kw.lower() for kw in args["keywords"]]
    categories_filter = args.get("categories")
    detail_level = args.get("detail_level", "full")

    tools = _load_tools()
    categories = _get_tool_categories()

    if categories_filter:
        names: List[str] = []
        for cat in categories_filter:
            names.extend(categories.get(cat, []))
        candidate_names = sorted(set(names))
    else:
        candidate_names = sorted(tools.keys())

    help_tools = _load_help()
    matches = []
    for name in candidate_names:
        tool = tools.get(name, {})
        help_item = help_tools.get(name, {})
        search_text = " ".join(
            [
                name,
                str(tool.get("description", "")),
                str(tool.get("usage", "")),
                str(help_item.get("title", "")),
                str(help_item.get("description", "")),
                " ".join(help_item.get("operations", []) or []),
                " ".join(help_item.get("actions", []) or []),
            ]
        ).lower()

        if any(keyword in search_text for keyword in keywords):
            matches.append(_tool_summary(name, detail_level))

    return {
        "matches": matches,
        "total_matches": len(matches),
        "keywords": args["keywords"],
        "categories_searched": categories_filter or "all",
        "detail_level": detail_level,
    }


def list_tools_by_category(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    category_filter = args.get("category")
    categories = _get_tool_categories()

    if category_filter:
        if category_filter not in categories:
            return {
                "error": f"Unknown category: {category_filter}",
                "available_categories": sorted(categories.keys()),
            }

        tools = categories[category_filter]
        return {
            "category": category_filter,
            "tools": tools,
            "tool_count": len(tools),
        }

    result = {"categories": {}, "total_tools": 0}
    for cat_name, tool_list in sorted(categories.items()):
        result["categories"][cat_name] = {
            "tools": tool_list,
            "count": len(tool_list),
        }
        result["total_tools"] += len(tool_list)

    return result


# Backward-compatible alias kept for external imports/tests.
def list_by_category(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    return list_tools_by_category(db, args)


def get_active_workflow(
    db: StandardDatabase, args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if args is None:
        args = {}
    session_state, session_id = _get_session_context(args)

    workflows = _load_workflows()
    contexts = workflows["contexts"]

    if session_state:
        active_context = session_state.get_active_workflow(session_id) or "baseline"
    else:
        active_context = "baseline"

    if active_context not in contexts:
        active_context = "baseline" if "baseline" in contexts else next(iter(contexts))

    context_info = contexts[active_context]
    tools = context_info.get("tools", [])

    return {
        "active_context": active_context,
        "description": context_info.get("description", ""),
        "tools": tools,
        "tool_count": len(tools),
    }


def list_workflows(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    session_state, session_id = _get_session_context(args)
    include_tools = args.get("include_tools", False)

    workflows = _load_workflows()
    contexts_def = workflows["contexts"]

    contexts: Dict[str, Any] = {}
    for context_name, context_info in contexts_def.items():
        tools = context_info.get("tools", [])
        contexts[context_name] = {
            "description": context_info.get("description", ""),
            "tool_count": len(tools),
        }
        if include_tools:
            contexts[context_name]["tools"] = tools

    if session_state:
        active_context = session_state.get_active_workflow(session_id) or "baseline"
    else:
        active_context = "baseline"

    if active_context not in contexts:
        active_context = "baseline" if "baseline" in contexts else next(iter(contexts), "baseline")

    return {
        "contexts": contexts,
        "total_contexts": len(contexts),
        "active_context": active_context,
    }


def get_tool_usage_stats(
    db: StandardDatabase, args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if args is None:
        args = {}
    session_state, session_id = _get_session_context(args)

    if session_state:
        tool_usage = session_state.get_tool_usage_stats(session_id)
        current_stage = session_state.get_tool_lifecycle_stage(session_id) or "setup"
    else:
        tool_usage = {}
        current_stage = "setup"

    stages = _load_workflows()["stages"]
    if current_stage not in stages:
        current_stage = "setup" if "setup" in stages else next(iter(stages), "setup")

    return {
        "current_stage": current_stage,
        "tool_usage": tool_usage,
        "total_tools_used": len(tool_usage),
        "active_stage_tools": stages.get(current_stage, {}).get("tools", []),
    }


# Backward-compatible alias kept for external imports/tests.
def usage_stats(
    db: StandardDatabase, args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return get_tool_usage_stats(db, args)


def unload_tools(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    _session_state, _session_id = _get_session_context(args)

    tool_names = args["tool_names"]
    available = set(_load_tools().keys())

    unloaded = []
    not_found = []
    for tool_name in tool_names:
        if tool_name in available:
            unloaded.append(tool_name)
        else:
            not_found.append(tool_name)

    return {
        "unloaded": unloaded,
        "not_found": not_found,
        "total_unloaded": len(unloaded),
    }
