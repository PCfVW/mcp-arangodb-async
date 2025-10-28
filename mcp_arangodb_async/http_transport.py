"""
HTTP Transport Implementation for MCP ArangoDB Server

This module implements Streamable HTTP transport using Starlette and the MCP SDK.
Supports both stateful and stateless operation modes with proper CORS configuration.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import uvicorn
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from .health import health_check

logger = logging.getLogger(__name__)


def create_health_route(app: Starlette) -> Route:
    """
    Create health check route for the HTTP server.

    Args:
        app: Starlette application instance (used to access app.state.db)

    Returns:
        Starlette Route for health endpoint
    """
    async def health_endpoint(request: Request) -> JSONResponse:
        """Health check endpoint handler."""
        try:
            # Access database from Starlette app state
            # This is set during server startup in run_http_server()
            db = getattr(app.state, "db", None)
            logger.debug(f"Health check: db from app.state = {db}")

            # Get health status
            status = await health_check(db)

            # Return appropriate HTTP status code
            http_status = 200 if status["status"] == "healthy" else 503

            return JSONResponse(status, status_code=http_status)
        except Exception as e:
            logger.error(f"Health check endpoint error: {e}")
            return JSONResponse(
                {"status": "unhealthy", "error": str(e)},
                status_code=503
            )

    return Route("/health", health_endpoint, methods=["GET"])


def create_http_app(
    mcp_server: Server,
    cors_origins: list[str] | None = None,
    stateless: bool = False,
) -> tuple[Starlette, StreamableHTTPSessionManager]:
    """
    Create Starlette application with MCP Streamable HTTP transport.
    
    Args:
        mcp_server: MCP Server instance
        cors_origins: List of allowed CORS origins (default: ["*"])
        stateless: Whether to run in stateless mode (default: False)
        
    Returns:
        Tuple of (Starlette app, StreamableHTTPSessionManager)
    """
    if cors_origins is None:
        cors_origins = ["*"]
    
    # Create StreamableHTTP session manager
    session_manager = StreamableHTTPSessionManager(
        mcp_server,
        stateless=stateless,
    )
    
    # Create Starlette app first (needed for health route)
    starlette_app = Starlette()

    # Create Starlette routes (health route needs app instance)
    routes = [
        create_health_route(starlette_app),
    ]

    # Add routes to app
    starlette_app.router.routes.extend(routes)

    # Mount MCP StreamableHTTP endpoint at /mcp
    # The session_manager.handle_request is an ASGI callable
    starlette_app.mount("/mcp", session_manager.handle_request)

    # Add CORS middleware
    # IMPORTANT: Mcp-Session-Id header must be exposed for browser clients
    # Note: We wrap the app with CORS middleware but return both the wrapped app
    # and the original Starlette app so we can access app.state
    cors_app = CORSMiddleware(
        starlette_app,
        allow_origins=cors_origins,
        allow_methods=["GET", "POST", "DELETE"],  # MCP streamable HTTP methods
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],  # Critical for session management
    )

    return cors_app, session_manager, starlette_app


async def run_http_server(
    mcp_server: Server,
    host: str = "0.0.0.0",
    port: int = 8000,
    stateless: bool = False,
    cors_origins: list[str] | None = None,
) -> None:
    """
    Run the MCP server with HTTP transport using uvicorn.

    Args:
        mcp_server: MCP Server instance
        host: Host address to bind to (default: "0.0.0.0")
        port: Port number to bind to (default: 8000)
        stateless: Whether to run in stateless mode (default: False)
        cors_origins: List of allowed CORS origins (default: ["*"])
    """
    logger.info(f"Starting MCP HTTP server on {host}:{port} (stateless={stateless})")

    # Import server_lifespan from entry module
    # We need to manually trigger the lifespan because StreamableHTTPSessionManager
    # does not automatically call the server's lifespan function
    from .entry import server_lifespan

    # Create Starlette app with MCP transport
    # Returns: (CORS-wrapped app, session_manager, original Starlette app)
    cors_app, session_manager, starlette_app = create_http_app(
        mcp_server,
        cors_origins=cors_origins,
        stateless=stateless,
    )

    # Create uvicorn config with CORS-wrapped app
    config = uvicorn.Config(
        cors_app,
        host=host,
        port=port,
        log_level="info",
        access_log=True,
    )

    # Create uvicorn server
    server = uvicorn.Server(config)

    # IMPORTANT: Manually enter the server's lifespan context
    # The StreamableHTTPSessionManager.run() does NOT automatically trigger
    # the MCP server's lifespan, so we need to do it explicitly here.
    # This ensures database connection is initialized before the server starts.
    async with server_lifespan(mcp_server) as lifespan_context:
        # Store database connection in Starlette app.state
        # This is the idiomatic way to share state across requests in Starlette
        # Note: We use the original Starlette app, not the CORS-wrapped one
        starlette_app.state.db = lifespan_context.get("db")
        logger.info(f"Stored database connection in app.state: {starlette_app.state.db}")

        # Run session manager and uvicorn server concurrently
        async with session_manager.run():
            logger.info(f"MCP HTTP server ready at http://{host}:{port}/mcp")
            logger.info(f"Health check endpoint at http://{host}:{port}/health")
            await server.serve()
