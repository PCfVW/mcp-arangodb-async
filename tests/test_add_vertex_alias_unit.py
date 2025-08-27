import pytest
from mcp_arangodb_async import entry as entry_mod
from mcp_arangodb_async.tools import ARANGO_ADD_VERTEX
from mcp_arangodb_async.models import InsertArgs


class DummyCollection:
    def __init__(self):
        self.inserted = []
    def insert(self, doc):
        self.inserted.append(doc)
        return {"_id": "users/1", "_key": "1", "_rev": "_rev"}


class DummyDB:
    def __init__(self):
        self._cols = {"users": DummyCollection()}
    def collection(self, name):
        return self._cols[name]


@pytest.mark.asyncio
async def test_arango_add_vertex_alias_routes_to_insert(monkeypatch):
    # patch server context with DummyDB
    server = entry_mod.server
    server.request_context = type("Ctx", (), {"lifespan_context": {"db": DummyDB()}})()

    # validate list_tools includes alias when full
    monkeypatch.setenv("MCP_COMPAT_TOOLSET", "full")
    tools = await entry_mod.handle_list_tools()
    assert any(t.name == ARANGO_ADD_VERTEX for t in tools)

    args = InsertArgs(collection="users", document={"name": "Alice"}).model_dump()
    content = await entry_mod.call_tool(ARANGO_ADD_VERTEX, args)
    # Expect JSON content with inserted metadata
    assert content and content[0].type == "text"
    # No exception indicates routing worked
