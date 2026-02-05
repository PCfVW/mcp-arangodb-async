"""Session utilities for multi-tenancy support.

This module provides session ID extraction for different MCP transports,
enabling consistent session identification across stdio and HTTP deployments.
"""

from typing import Any, Optional


def extract_session_id(request_context: Any) -> str:
    """Extract session ID from request context.
    
    Handles different MCP transport types:
    - stdio: Returns "stdio" (singleton session per subprocess)
    - HTTP: Returns unique identifier from request session
    
    Args:
        request_context: MCP request context object
        
    Returns:
        Session identifier string:
        - "stdio" for stdio transport
        - Unique session ID for HTTP transport
    """
    # Check for HTTP transport with session
    if hasattr(request_context, "session") and request_context.session:
        # HTTP transport: extract session ID from request
        if hasattr(request_context.session, "session_id"):
            session_id = request_context.session.session_id
            if session_id:
                return session_id
    
    # Default to stdio transport (singleton session)
    return "stdio"

