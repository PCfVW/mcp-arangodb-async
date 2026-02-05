#!/usr/bin/env python3
"""
MCP Inspector convenience script for debugging the ArangoDB MCP server.

This script launches the MCP Inspector with the correct configuration
to debug the arango-server MCP stdio server.

Prerequisites:
- Node.js installed
- MCP Inspector: npm install -g @modelcontextprotocol/inspector
- Environment variables set (ARANGO_URL, ARANGO_DB, etc.)
"""

import os
import subprocess
import sys
import tempfile
import json
from pathlib import Path


def get_server_config():
    """Generate MCP Inspector server configuration."""
    return {
        "command": "python",
        "args": ["-m", "mcp_arangodb_async.entry"],
        "env": {
            "ARANGO_URL": os.getenv("ARANGO_URL", "http://localhost:8529"),
            "ARANGO_DB": os.getenv("ARANGO_DB", "mcp_arangodb_test"),
            "ARANGO_USERNAME": os.getenv("ARANGO_USERNAME", "mcp_arangodb_user"),
            "ARANGO_PASSWORD": os.getenv("ARANGO_PASSWORD", "mcp_arangodb_password"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "WARNING"),
            "ARANGO_CONNECT_RETRIES": os.getenv("ARANGO_CONNECT_RETRIES", "5"),
            "ARANGO_CONNECT_DELAY_SEC": os.getenv("ARANGO_CONNECT_DELAY_SEC", "1.0"),
        }
    }


def check_inspector_installed():
    """Check if MCP Inspector is installed."""
    try:
        result = subprocess.run(
            ["npx", "@modelcontextprotocol/inspector", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def main():
    """Launch MCP Inspector for the ArangoDB MCP server."""
    print("🔍 MCP Inspector for ArangoDB MCP Server")
    print("=" * 50)
    
    # Check if Inspector is available
    if not check_inspector_installed():
        print("❌ MCP Inspector not found!")
        print("\nTo install MCP Inspector:")
        print("  npm install -g @modelcontextprotocol/inspector")
        print("\nOr run with npx (no installation required):")
        print("  npx @modelcontextprotocol/inspector")
        return 1
    
    # Check environment variables
    required_vars = ["ARANGO_URL", "ARANGO_DB", "ARANGO_USERNAME", "ARANGO_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
        print("\nExample setup:")
        print("  export ARANGO_URL=http://localhost:8529")
        print("  export ARANGO_DB=mcp_arangodb_test")
        print("  export ARANGO_USERNAME=mcp_arangodb_user")
        print("  export ARANGO_PASSWORD=mcp_arangodb_password")
        print("\nContinuing with defaults where possible...")
    
    # Generate server config
    config = get_server_config()
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f, indent=2)
        config_path = f.name
    
    try:
        print(f"\n🚀 Launching MCP Inspector...")
        print(f"Server command: {config['command']} {' '.join(config['args'])}")
        print(f"Environment: {list(config['env'].keys())}")
        print("\nThe Inspector will open in your browser.")
        print("Use Ctrl+C to stop.\n")
        
        # Launch Inspector
        cmd = ["npx", "@modelcontextprotocol/inspector", config_path]
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch MCP Inspector: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Inspector stopped by user")
        return 0
    finally:
        # Clean up temp file
        try:
            os.unlink(config_path)
        except OSError:
            pass
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
