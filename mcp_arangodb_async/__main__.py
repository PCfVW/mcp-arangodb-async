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

from .config import load_config
from .db import get_client_and_db, health_check


def main() -> int:
    parser = argparse.ArgumentParser(prog="mcp_arangodb_async", description="ArangoDB MCP diagnostics")
    parser.add_argument("command", nargs="?", choices=["health", "server"], help="Command to run (default: server)")
    parser.add_argument("--health", dest="health_flag", action="store_true", help="Run health check and output JSON")
    parser.add_argument("--server", dest="server_flag", action="store_true", help="Run MCP server (default when no args)")
    args = parser.parse_args()

    # Determine mode: if no command and no flags, default to MCP server
    run_health = args.command == "health" or args.health_flag
    run_server = args.command == "server" or args.server_flag or (args.command is None and not args.health_flag)

    # Delegate to MCP server entry point
    if run_server:
        try:
            from .entry import main as entry_main
            entry_main()  # This never returns (runs async event loop)
            return 0
        except ImportError as e:
            print(f"Error: Could not import MCP server entry point: {e}", file=sys.stderr)
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
            print(json.dumps({
                "ok": True,
                "url": cfg.arango_url,
                "db": cfg.database,
                "user": cfg.username,
                "info": info,
            }, ensure_ascii=False))
        else:
            version = db.version()
            print(f"Connected to ArangoDB {version} at {cfg.arango_url}, DB='{cfg.database}' as user '{cfg.username}'")
            # Optional: quick sanity query to list collections
            try:
                cols = [c['name'] for c in db.collections() if not c.get('isSystem')]
                print(f"Non-system collections: {cols}")
            except Exception as e:
                # Collection listing failed, but don't crash the health check
                print(f"Warning: Could not list collections: {e}")
        client.close()
        return 0
    except Exception as e:
        if run_health:
            print(json.dumps({
                "ok": False,
                "error": str(e),
                "url": cfg.arango_url,
                "db": cfg.database,
                "user": cfg.username,
            }, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"Connection failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
