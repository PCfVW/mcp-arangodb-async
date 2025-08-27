import types
from mcp_arangodb_async.handlers import (
    handle_create_graph,
    handle_add_edge,
    handle_traverse,
    handle_shortest_path,
)


class DummyCollection:
    def __init__(self):
        self.insert_calls = []

    def insert(self, payload):
        self.insert_calls.append(payload)
        return {"_id": "edges/1", "_key": "1", "_rev": "_rev"}


class DummyAQL:
    def __init__(self):
        self.last_query = None
        self.last_bind = None
        self.result = []

    def execute(self, query, bind_vars=None, **kwargs):
        self.last_query = query
        self.last_bind = bind_vars or {}
        # Return an iterator protocol like arango does
        return iter(self.result)


class DummyDB:
    def __init__(self):
        self._collections = set()
        self._graphs = set()
        self._created_graphs = []
        self.aql = DummyAQL()
        self._collections_handles = {}

    # collections
    def has_collection(self, name):
        return name in self._collections

    def create_collection(self, name, edge=False, **kwargs):
        self._collections.add(name)
        col = DummyCollection()
        self._collections_handles[name] = col
        return col

    def collection(self, name):
        if name not in self._collections_handles:
            self._collections_handles[name] = DummyCollection()
        return self._collections_handles[name]

    # graphs
    def has_graph(self, name):
        return name in self._graphs

    def create_graph(self, name, edge_definitions=None, **kwargs):
        self._graphs.add(name)
        self._created_graphs.append((name, edge_definitions or []))
        return types.SimpleNamespace(name=name)

    def graph(self, name):
        return types.SimpleNamespace(name=name)


def test_handle_create_graph_creates_resources():
    db = DummyDB()
    args = {
        "name": "g1",
        "edge_definitions": [
            {
                "edge_collection": "edges",
                "from_collections": ["users"],
                "to_collections": ["orders"],
            }
        ],
        "create_collections": True,
    }
    info = handle_create_graph(db, args)
    assert info["name"] == "g1"
    assert db.has_graph("g1")
    # collections created
    assert db.has_collection("edges")
    assert db.has_collection("users")
    assert db.has_collection("orders")


def test_handle_add_edge_inserts_document():
    db = DummyDB()
    db.create_collection("edges", edge=True)
    out = handle_add_edge(
        db,
        {
            "collection": "edges",
            "from_id": "users/1",
            "to_id": "orders/2",
            "attributes": {"type": "PLACED"},
        },
    )
    assert out["_id"] == "edges/1"
    col = db.collection("edges")
    assert col.insert_calls, "edge insert should be called"
    assert col.insert_calls[0]["_from"] == "users/1"
    assert col.insert_calls[0]["_to"] == "orders/2"
    assert col.insert_calls[0]["type"] == "PLACED"


def test_handle_traverse_with_graph_uses_graph_binding():
    db = DummyDB()
    db.aql.result = [{"vertex": {"_id": "users/1"}}]
    res = handle_traverse(
        db,
        {
            "start_vertex": "users/1",
            "graph": "g1",
            "direction": "OUTBOUND",
            "min_depth": 1,
            "max_depth": 2,
            "return_paths": False,
            "limit": 5,
        },
    )
    assert res and isinstance(res, list)
    assert "GRAPH @graph" in db.aql.last_query
    assert db.aql.last_bind["graph"] == "g1"
    assert db.aql.last_bind["start"] == "users/1"
    assert db.aql.last_bind["limit"] == 5


def test_handle_shortest_path_with_edge_collections():
    db = DummyDB()
    db.aql.result = [{"vertices": [{"_id": "users/1"}], "edges": []}]
    res = handle_shortest_path(
        db,
        {
            "start_vertex": "users/1",
            "end_vertex": "users/9",
            "edge_collections": ["follows"],
            "direction": "ANY",
            "return_paths": True,
        },
    )
    assert res["found"] is True
    assert "SHORTEST_PATH" in db.aql.last_query
    assert "follows" in db.aql.last_query
    assert db.aql.last_bind["start"] == "users/1"
    assert db.aql.last_bind["end"] == "users/9"
