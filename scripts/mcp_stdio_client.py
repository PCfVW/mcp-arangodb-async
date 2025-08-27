from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


async def run() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="MCP stdio client for ArangoDB")
    parser.add_argument("--demo", action="store_true", help="Run a mini CRUD demo (create collection, insert, query)")
    parser.add_argument("--collection", default="users", help="Collection name for demo (default: users)")
    args = parser.parse_args()
    # Configure server launch: use Python to run our stdio server module
    env = os.environ.copy()
    # Ensure ARANGO_* are present (fallbacks mirror env.example)
    env.setdefault("ARANGO_URL", "http://localhost:8529")
    env.setdefault("ARANGO_DB", "mcp_arangodb_test")
    env.setdefault("ARANGO_USERNAME", "mcp_arangodb_user")
    env.setdefault("ARANGO_PASSWORD", "mcp_arangodb_password")
    # Do not set ARANGO_CONNECT_* defaults here; rely on process/.env or server defaults

    # Launch the child server with the same interpreter to avoid PATH/launcher differences
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_arangodb_async.entry"],
        env=env,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # Basic debug of environment being used by the server (do not print passwords)
            print(f"Starting MCP server with {sys.executable} and env: ARANGO_URL={env.get('ARANGO_URL')} ARANGO_DB={env.get('ARANGO_DB')} ARANGO_USERNAME={env.get('ARANGO_USERNAME')} RETRIES={env.get('ARANGO_CONNECT_RETRIES')} DELAY={env.get('ARANGO_CONNECT_DELAY_SEC')}")

            # List tools
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            # Optional demo flow
            if args.demo:
                # 1) Ensure collection exists
                if any(t.name == "arango_create_collection" for t in tools.tools):
                    create_res = await session.call_tool(
                        "arango_create_collection",
                        arguments={"name": args.collection, "type": "document"},
                    )
                    if create_res.content and isinstance(create_res.content[0], types.TextContent):
                        print(f"Create collection result: {create_res.content[0].text}")

                # 2) Insert a sample document
                if any(t.name == "arango_insert" for t in tools.tools):
                    doc = {"name": "Alice", "ts": __import__("time").time()}
                    insert_res = await session.call_tool(
                        "arango_insert",
                        arguments={"collection": args.collection, "document": doc},
                    )
                    if insert_res.content and isinstance(insert_res.content[0], types.TextContent):
                        print(f"Insert result: {insert_res.content[0].text}")

                # 3) Query the documents
                if any(t.name == "arango_query" for t in tools.tools):
                    q = f"FOR d IN {args.collection} RETURN d"
                    query_res = await session.call_tool(
                        "arango_query",
                        arguments={"query": q},
                    )
                    if query_res.content and isinstance(query_res.content[0], types.TextContent):
                        try:
                            rows = json.loads(query_res.content[0].text)
                            print("Query rows:", json.dumps(rows, ensure_ascii=False))
                        except Exception:
                            print("Query (raw):", query_res.content[0].text)
            else:
                # Default: list collections
                if any(t.name == "arango_list_collections" for t in tools.tools):
                    result = await session.call_tool("arango_list_collections", arguments={})
                    if result.content and isinstance(result.content[0], types.TextContent):
                        try:
                            parsed = json.loads(result.content[0].text)
                            print("Collections:", json.dumps(parsed, ensure_ascii=False))
                        except Exception:
                            print("Collections (raw):", result.content[0].text)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
