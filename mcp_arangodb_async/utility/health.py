"""
Health Check Endpoint for MCP ArangoDB Server

This module provides health check functionality for monitoring server status.
Returns database connectivity status and server information.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from arango.database import StandardDatabase

logger = logging.getLogger(__name__)


async def health_check(db: StandardDatabase | None) -> Dict[str, Any]:
    """
    Check server and database health status.
    
    Args:
        db: ArangoDB database instance (may be None if connection failed)
        
    Returns:
        Dictionary containing health status information:
        - status: "healthy" or "unhealthy"
        - database_connected: Boolean indicating database connectivity
        - database_info: Database version and details (if connected)
        - error: Error message (if unhealthy)
    """
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "database_connected": False,
    }
    
    # Check database connectivity
    if db is None:
        health_status["status"] = "unhealthy"
        health_status["error"] = "Database connection not established"
        logger.warning("Health check: Database connection is None")
        return health_status
    
    try:
        # Test database connectivity by getting version
        version = db.version()
        health_status["database_connected"] = True
        health_status["database_info"] = {
            "version": version,
            "name": db.name,
        }
        logger.debug(f"Health check: Database connected (version: {version})")
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database_connected"] = False
        health_status["error"] = f"Database connectivity check failed: {str(e)}"
        logger.error(f"Health check failed: {e}")
    
    return health_status

