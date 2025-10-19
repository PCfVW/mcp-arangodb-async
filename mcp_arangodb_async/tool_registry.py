"""
Tool Registry for MCP ArangoDB Server

This module provides a centralized registry for tool metadata and routing.
It replaces the previous hybrid approach (model map + if-elif chain + manual tool list)
with a single source of truth for tool definitions.

Key Components:
- ToolRegistration: Dataclass holding tool metadata (name, description, model, handler)
- TOOL_REGISTRY: Global dictionary mapping tool names to ToolRegistration objects
- register_tool(): Decorator for registering tools with duplicate detection

Usage:
    from .tool_registry import TOOL_REGISTRY, ToolRegistration
    
    # Manual registration (Phase 1)
    TOOL_REGISTRY["arango_query"] = ToolRegistration(
        name="arango_query",
        description="Execute an AQL query",
        model=QueryArgs,
        handler=handle_arango_query,
    )
    
    # Future decorator usage (Phase 2)
    @register_tool(
        name="arango_query",
        description="Execute an AQL query",
        model=QueryArgs,
    )
    def handle_arango_query(db, args):
        ...
"""

from dataclasses import dataclass
from typing import Callable, Dict, Type
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolRegistration:
    """Metadata for a registered MCP tool.

    Attributes:
        name: Tool name (e.g., "arango_query")
        description: Human-readable description for MCP clients
        model: Pydantic model class for argument validation
        handler: Handler function that executes the tool logic (stored as reference for Phase 1)
    """
    name: str
    description: str
    model: Type[BaseModel]
    handler: Callable

    def get_handler(self) -> Callable:
        """Get the handler function.

        Returns the handler function reference. In Phase 1, this is a direct reference.
        In future phases with decorators, this could be enhanced to support dynamic lookup
        for better test compatibility.

        Returns:
            Handler function
        """
        return self.handler


# Global registry: maps tool name -> ToolRegistration
TOOL_REGISTRY: Dict[str, ToolRegistration] = {}


def register_tool(
    name: str,
    description: str,
    model: Type[BaseModel],
) -> Callable:
    """Decorator to register a tool handler with the MCP server.
    
    This decorator provides a declarative way to register tools, ensuring
    all metadata is defined in one place. It includes duplicate detection
    to prevent accidental overwrites.
    
    Args:
        name: Tool name (must be unique)
        description: Human-readable description
        model: Pydantic model for argument validation
        
    Returns:
        Decorator function that registers the handler
        
    Raises:
        ValueError: If a tool with the same name is already registered
        
    Example:
        @register_tool(
            name="arango_query",
            description="Execute an AQL query",
            model=QueryArgs,
        )
        def handle_arango_query(db, args):
            return {"result": "..."}
    """
    def decorator(handler: Callable) -> Callable:
        # Check for duplicate registration
        if name in TOOL_REGISTRY:
            existing = TOOL_REGISTRY[name]
            raise ValueError(
                f"Tool '{name}' is already registered by handler "
                f"'{existing.handler.__name__}' in module '{existing.handler.__module__}'. "
                f"Cannot register duplicate handler '{handler.__name__}' "
                f"in module '{handler.__module__}'."
            )
        
        # Register in global registry
        TOOL_REGISTRY[name] = ToolRegistration(
            name=name,
            description=description,
            model=model,
            handler=handler,
        )
        
        logger.debug(f"Registered tool: {name} -> {handler.__name__}")
        return handler
    
    return decorator


def validate_registry(expected_tools: list[str] | None = None) -> None:
    """Validate that all expected tools are registered.
    
    This function should be called during server startup to ensure
    the registry is properly populated before handling requests.
    
    Args:
        expected_tools: Optional list of tool names that must be registered.
                       If None, only checks that registry is non-empty.
                       
    Raises:
        RuntimeError: If registry validation fails
        
    Example:
        # In server_lifespan():
        validate_registry([
            "arango_query",
            "arango_list_collections",
            # ... all expected tools
        ])
    """
    if not TOOL_REGISTRY:
        raise RuntimeError(
            "Tool registry is empty. No tools have been registered. "
            "Ensure tool registration happens before server startup."
        )
    
    if expected_tools is not None:
        registered = set(TOOL_REGISTRY.keys())
        expected = set(expected_tools)
        
        missing = expected - registered
        if missing:
            raise RuntimeError(
                f"Tool registry validation failed. Missing tools: {sorted(missing)}. "
                f"Registered tools: {sorted(registered)}"
            )
        
        extra = registered - expected
        if extra:
            logger.warning(
                f"Tool registry contains unexpected tools: {sorted(extra)}. "
                f"Expected tools: {sorted(expected)}"
            )
    
    logger.info(f"Tool registry validated: {len(TOOL_REGISTRY)} tools registered")

