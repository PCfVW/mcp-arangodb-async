import asyncio
import os
import types
import pytest

from mcp_arangodb_async.handlers import (
    handle_list_graphs,
    handle_add_vertex_collection,
    handle_add_edge_definition,
)
from mcp_arangodb_async.tools import (
    ARANGO_TRAVERSE,
    ARANGO_GRAPH_TRAVERSAL,
)
from mcp_arangodb_async import entry as entry_mod


class DummyGraph:
    def __init__(self, name):
        self.name = name
        self.add_vertex_calls = []
        self.edge_defs = []

    def add_vertex_collection(self, name):
        self.add_vertex_calls.append(name)

    def create_edge_definition(self, edge_collection=None, from_vertex_collections=None, to_vertex_collections=None):
        self.edge_defs.append(
            {
                "edge_collection": edge_collection,
                "from_vertex_collections": from_vertex_collections or [],
                "to_vertex_collections": to_vertex_collections or [],
            }
        )


class DummyDB:
    def __init__(self):
        self._graphs = [
            {"name": "g1"},
            {"name": "g2"},
        ]
        self._graph_objs = {}

    def graphs(self):
        return list(self._graphs)

    def graph(self, name):
        if name not in self._graph_objs:
            self._graph_objs[name] = DummyGraph(name)
        return self._graph_objs[name]


def test_handle_list_graphs_returns_names():
    db = DummyDB()
    out = handle_list_graphs(db, {})
    names = [g["name"] for g in out]
    assert names == ["g1", "g2"]


def test_add_vertex_collection_records_call():
    db = DummyDB()
    res = handle_add_vertex_collection(db, {"graph": "g1", "collection": "users"})
    assert res["graph"] == "g1"
    assert res["collection_added"] == "users"
    g = db.graph("g1")
    assert g.add_vertex_calls == ["users"]


def test_add_edge_definition_records_definition():
    db = DummyDB()
    res = handle_add_edge_definition(
        db,
        {
            "graph": "g1",
            "edge_collection": "edges",
            "from_collections": ["users"],
            "to_collections": ["orders"],
        },
    )
    assert res["graph"] == "g1"
    ed = res["edge_definition"]
    assert ed["edge_collection"] == "edges"
    assert ed["from_collections"] == ["users"]
    assert ed["to_collections"] == ["orders"]
    g = db.graph("g1")
    assert g.edge_defs and g.edge_defs[0]["edge_collection"] == "edges"


@pytest.mark.asyncio
async def test_list_tools_includes_traversal_alias_when_full(monkeypatch):
    # Ensure full toolset exposure
    monkeypatch.setenv("MCP_COMPAT_TOOLSET", "full")
    tools = await entry_mod.handle_list_tools()
    names = {t.name for t in tools}
    assert ARANGO_TRAVERSE in names
    assert ARANGO_GRAPH_TRAVERSAL in names
