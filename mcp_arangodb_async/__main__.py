"""
ArangoDB MCP Server - Command Line Interface

This module provides a command-line interface for ArangoDB diagnostics and health checks.
Can be run as: python -m mcp_arangodb_async [command]

Functions:
- main() - Main entry point for command line execution
"""

from __future__ import annotations

import sys
import json
import argparse
import os

from .config import load_config
from .db import get_client_and_db, health_check


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="mcp_arangodb_async",
        description="ArangoDB MCP Server with stdio and HTTP transport support",
    )

    # Existing arguments
    parser.add_argument(
        "command",
        nargs="?",
        choices=["health", "server"],
        help="Command to run (default: server)",
    )
    parser.add_argument(
        "--health",
        dest="health_flag",
        action="store_true",
        help="Run health check and output JSON",
    )
    parser.add_argument(
        "--server",
        dest="server_flag",
        action="store_true",
        help="Run MCP server (default when no args)",
    )

    # NEW: Transport arguments
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=None,
        help="Transport type (default: stdio, or from MCP_TRANSPORT env var)",
    )
    parser.add_argument(
        "--host",
        default=None,
        help="HTTP host (default: 0.0.0.0, or from MCP_HTTP_HOST env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="HTTP port (default: 8000, or from MCP_HTTP_PORT env var)",
    )
    parser.add_argument(
        "--stateless", action="store_true", help="Run HTTP in stateless mode"
    )

    args = parser.parse_args()

    # Determine mode: if no command and no flags, default to MCP server
    run_health = args.command == "health" or args.health_flag
    run_server = (
        args.command == "server"
        or args.server_flag
        or (args.command is None and not args.health_flag)
    )

    # Delegate to MCP server entry point
    if run_server:
        try:
            from .entry import main as entry_main

            # NEW: Build transport config from args and env vars
            transport = args.transport or os.getenv("MCP_TRANSPORT", "stdio")

            if transport == "http":
                # Only import TransportConfig if HTTP transport is requested
                from .transport_config import TransportConfig

                transport_config = TransportConfig(
                    transport="http",
                    http_host=args.host or os.getenv("MCP_HTTP_HOST", "0.0.0.0"),
                    http_port=args.port or int(os.getenv("MCP_HTTP_PORT", "8000")),
                    http_stateless=args.stateless
                    or os.getenv("MCP_HTTP_STATELESS", "false").lower() == "true",
                    http_cors_origins=os.getenv("MCP_HTTP_CORS_ORIGINS", "*").split(
                        ","
                    ),
                )
                entry_main(transport_config)
            else:
                # Default stdio transport - no config needed
                entry_main()

            return 0
        except ImportError as e:
            print(
                f"Error: Could not import MCP server entry point: {e}", file=sys.stderr
            )
            print("Please ensure the package is properly installed.", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error starting MCP server: {e}", file=sys.stderr)
            return 1

    cfg = load_config()

    # CLI diagnostic mode (health check or info)
    try:
        client, db = get_client_and_db(cfg)
        if run_health:
            info = health_check(db)
            print(
                json.dumps(
                    {
                        "ok": True,
                        "url": cfg.arango_url,
                        "db": cfg.database,
                        "user": cfg.username,
                        "info": info,
                    },
                    ensure_ascii=False,
                )
            )
        else:
            version = db.version()
            print(
                f"Connected to ArangoDB {version} at {cfg.arango_url}, DB='{cfg.database}' as user '{cfg.username}'"
            )
            # Optional: quick sanity query to list collections
            try:
                cols = [c["name"] for c in db.collections() if not c.get("isSystem")]
                print(f"Non-system collections: {cols}")
            except Exception as e:
                # Collection listing failed, but don't crash the health check
                print(f"Warning: Could not list collections: {e}")
        client.close()
        return 0
    except Exception as e:
        if run_health:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": str(e),
                        "url": cfg.arango_url,
                        "db": cfg.database,
                        "user": cfg.username,
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
        else:
            print(f"Connection failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
