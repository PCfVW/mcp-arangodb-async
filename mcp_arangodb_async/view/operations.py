"""ArangoSearch view operations."""

from typing import Any, Dict, List, Optional
from arango.database import StandardDatabase


def create_view(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Create an ArangoSearch view.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing view name, type, and properties

    Returns:
        Dictionary with view creation result

    Operator model:
      Preconditions:
        - Database connection available.
        - View name provided and valid.
      Effects:
        - Creates the view with specified configuration.
        - Mutates database.
    """
    name = args["name"]
    view_type = args.get("type", "arangosearch")
    properties = args.get("properties", {})

    try:
        # Create view
        view = db.create_view(name, view_type=view_type, properties=properties)
        return {
            "success": True,
            "name": name,
            "type": view_type,
            "view": view,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": "ViewCreationError",
            "name": name,
        }


def drop_view(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Drop an ArangoSearch view.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing view name

    Returns:
        Dictionary with drop result
    """
    name = args["name"]

    try:
        db.delete_view(name)
        return {
            "success": True,
            "name": name,
            "action": "dropped",
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": "ViewDropError",
            "name": name,
        }


def list_views(db: StandardDatabase, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """List all ArangoSearch views in the database.

    Returns:
        Dictionary with list of views
    """
    try:
        views = db.views()
        return {
            "success": True,
            "count": len(views),
            "views": views,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": "ViewListError",
        }


def get_view(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Get view properties.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing view name

    Returns:
        Dictionary with view properties
    """
    name = args["name"]

    try:
        view = db.view(name)
        properties = view.properties()
        return {
            "success": True,
            "name": name,
            "properties": properties,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": "ViewGetError",
            "name": name,
        }


def update_view(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Update view properties.

    Args:
        db: ArangoDB database instance
        args: Dictionary containing view name and new properties

    Returns:
        Dictionary with update result
    """
    name = args["name"]
    properties = args.get("properties", {})

    try:
        view = db.view(name)
        result = view.update(properties)
        return {
            "success": True,
            "name": name,
            "result": result,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": "ViewUpdateError",
            "name": name,
        }


def search_view(db: StandardDatabase, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a search query against an ArangoSearch view.

    Args:
        db: ArangoDB database instance
        args: Dictionary with view name, AQL query (or search parameters)

    Returns:
        Dictionary with search results
    """
    name = args["name"]
    query = args.get("query")
    bind_vars = args.get("bind_vars", {})

    try:
        if not query:
            return {
                "error": "query parameter required for search",
                "type": "MissingParameter",
            }

        # Execute AQL query against view
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        results = list(cursor)

        return {
            "success": True,
            "view": name,
            "count": len(results),
            "results": results,
        }
    except Exception as e:
        return {
            "error": str(e),
            "type": "SearchError",
            "view": name,
        }
