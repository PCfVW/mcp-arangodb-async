from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Dict

import pytest
from arango import ArangoClient

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


INTEGRATION_FLAG = os.getenv("RUN_INTEGRATION_TESTS", "0") == "1"
ARANGO_URL = os.getenv("ARANGO_URL", "http://localhost:8529")
ROOT_PASSWORD = os.getenv("ARANGO_ROOT_PASSWORD", "changeme")
DB_NAME = os.getenv("ARANGO_DB", "mcp_arangodb_test")
APP_USER = os.getenv("ARANGO_USERNAME", "mcp_arangodb_user")
APP_PASS = os.getenv("ARANGO_PASSWORD", "mcp_arangodb_password")


pytestmark = pytest.mark.skipif(
    not INTEGRATION_FLAG,
    reason="Integration tests are skipped unless RUN_INTEGRATION_TESTS=1",
)


@pytest.fixture(scope="session")
def arango_env() -> Dict[str, str]:
    # Prepare database and user using root
    client = ArangoClient(hosts=ARANGO_URL)
    sys_db = client.db("_system", username="root", password=ROOT_PASSWORD)

    # create database if missing
    if not sys_db.has_database(DB_NAME):
        sys_db.create_database(DB_NAME)

    # create user and grant access
    if not sys_db.has_user(APP_USER):
        sys_db.create_user(APP_USER, APP_PASS)
    # set grant
    sys_db.update_permission(APP_USER, DB_NAME, permission="rw")

    # ensure a clean basic collection exists
    app_db = client.db(DB_NAME, username=APP_USER, password=APP_PASS)
    if not app_db.has_collection("itest"):
        app_db.create_collection("itest")

    return {
        "ARANGO_URL": ARANGO_URL,
        "ARANGO_DB": DB_NAME,
        "ARANGO_USERNAME": APP_USER,
        "ARANGO_PASSWORD": APP_PASS,
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "WARNING"),
        "ARANGO_CONNECT_RETRIES": os.getenv("ARANGO_CONNECT_RETRIES", "10"),
        "ARANGO_CONNECT_DELAY_SEC": os.getenv("ARANGO_CONNECT_DELAY_SEC", "1.0"),
    }


async def _run_with_session(env: Dict[str, str], coro):
    server_params = StdioServerParameters(
        command="py",
        args=["-m", "mcp_arangodb_async.entry"],
        env=env,
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await coro(session)


@pytest.mark.asyncio
async def test_list_tools_and_collections(arango_env):
    async def body(session: ClientSession):
        # list tools
        tools = await session.list_tools()
        names = sorted([t.name for t in tools.tools])
        assert "arango_list_collections" in names
        # call list collections
        result = await session.call_tool("arango_list_collections", arguments={})
        assert result.content, "expected content"
        block = result.content[0]
        assert isinstance(block, types.TextContent)
        # Not strictly parsing JSON here; just ensure some output present
        assert len(block.text) > 0
        return True

    ok = await _run_with_session(arango_env, body)
    assert ok is True


@pytest.mark.asyncio
async def test_insert_query_remove_roundtrip(arango_env):
    async def body(session: ClientSession):
        # ensure collection exists via create tool
        await session.call_tool("arango_create_collection", arguments={"name": "itest"})

        # insert a doc
        ins = await session.call_tool(
            "arango_insert",
            arguments={"collection": "itest", "document": {"_key": "k1", "v": 1}},
        )
        assert ins.content and isinstance(ins.content[0], types.TextContent)

        # query it back
        q = await session.call_tool(
            "arango_query",
            arguments={
                "query": "FOR d IN itest FILTER d._key == @k RETURN d",
                "bind_vars": {"k": "k1"},
            },
        )
        assert q.content and isinstance(q.content[0], types.TextContent)
        # remove it
        rm = await session.call_tool(
            "arango_remove",
            arguments={"collection": "itest", "key": "k1"},
        )
        assert rm.content and isinstance(rm.content[0], types.TextContent)
        return True

    ok = await _run_with_session(arango_env, body)
    assert ok is True
