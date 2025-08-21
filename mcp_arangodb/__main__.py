"""
ArangoDB MCP Server - Command Line Interface

This module provides a command-line interface for ArangoDB diagnostics and health checks.
Can be run as: python -m mcp_arangodb [command]

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
    parser = argparse.ArgumentParser(prog="mcp_arangodb", description="ArangoDB MCP diagnostics")
    parser.add_argument("command", nargs="?", choices=["health"], help="Command to run (default: info)")
    parser.add_argument("--health", dest="health_flag", action="store_true", help="Run health check and output JSON")
    args = parser.parse_args()

    cfg = load_config()

    # Determine mode
    run_health = args.command == "health" or args.health_flag

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
