"""
Template Handler - Pure Execution

Executes templates from config/templates/*.json. Auto-logs access.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from arango.database import StandardDatabase

from ..utility.access_log import log_query_results, ACCESS_TYPE_TEMPLATE
from ..utility.output import format_output, format_find_compact

logger = logging.getLogger(__name__)

# Config path - relative to package root
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "config" / "templates"

# Cache
_templates_cache: Optional[Dict[str, Dict]] = None


def load_templates() -> Dict[str, Dict]:
    """Load all templates (cached on demand)."""
    global _templates_cache
    if _templates_cache is None:
        _templates_cache = {}

        # Load all template categories
        for template_file in TEMPLATES_DIR.glob("*.json"):
            try:
                with open(template_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    category = data.get("category", template_file.stem)
                    templates = data.get("templates", {})

                    # Add to cache: category.name -> template
                    for name, template in templates.items():
                        full_name = f"{category}.{name}"
                        _templates_cache[full_name] = {
                            "name": full_name,
                            "category": category,
                            "query": template["query"],
                            "description": template.get("description", ""),
                            "params": template.get("params", {})
                        }
            except Exception as e:
                logger.error(f"Failed to load template {template_file}: {e}")

    return _templates_cache


def handle_template(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute query template.

    Args:
        db: ArangoDB database instance
        args: TemplateArgs

    Returns:
        Query results
    """
    name = args["name"]
    params = args.get("params") or {}

    try:
        templates = load_templates()

        # Get template
        template = templates.get(name)
        if not template:
            # List available
            available = sorted(templates.keys())
            return {"error": f"Template '{name}' not found", "available": available}

        # Get query and params schema
        query = template["query"]
        param_schema = template.get("params", {})

        # Build bind_vars
        bind_vars = {}

        for key, spec in param_schema.items():
            # Handle param spec
            if isinstance(spec, dict):
                # Check required
                if spec.get("required") and key not in params:
                    return {
                        "template": name,
                        "error": f"Missing required parameter: {key}"
                    }

                # Use provided value or default
                value = params.get(key, spec.get("default"))

                # Type conversion (basic)
                param_type = spec.get("type")
                if param_type == "int" and value is not None:
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        return {
                            "template": name,
                            "error": f"Parameter '{key}' must be int, got {type(value).__name__}"
                        }
                elif param_type == "number" and value is not None:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        return {
                            "template": name,
                            "error": f"Parameter '{key}' must be number, got {type(value).__name__}"
                        }

                bind_vars[key] = value

        # Handle @@ collection names (AQL bind var syntax for collection names)
        # Build separately to avoid RuntimeError from mutating dict during iteration
        collection_vars = {
            f"@{key}": value
            for key, value in list(bind_vars.items())
            if key.endswith("_collection")
        }
        # Remove original keys and add prefixed versions
        for key in collection_vars:
            original_key = key[1:]  # strip leading @
            bind_vars.pop(original_key, None)
        bind_vars.update(collection_vars)

        # Execute query
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)

        # Log access
        log_query_results(db, results, ACCESS_TYPE_TEMPLATE)

        return format_output({
            "template": name,
            "count": len(results),
            "results": results
        })

    except Exception as e:
        logger.error(f"Template execution failed: {e}")
        return {
            "template": name,
            "error": str(e)
        }
