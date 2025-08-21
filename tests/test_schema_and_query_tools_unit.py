import pytest

from mcp_arangodb.handlers import (
    handle_create_schema,
    handle_validate_document,
    handle_query_builder,
    handle_query_profile,
)


class DummySchemasCollection:
    def __init__(self):
        self.docs = {}
    def has(self, key):
        return key in self.docs
    def insert(self, doc):
        self.docs[doc["_key"]] = doc
        return {"_key": doc["_key"]}
    def replace(self, doc):
        self.docs[doc["_key"]] = doc
        return {"_key": doc["_key"]}
    def get(self, key):
        return self.docs.get(key)


class DummyAQL:
    def __init__(self, data=None, explain=None):
        self._data = data or []
        self._explain = explain or {"plans": [], "warnings": [], "stats": {}}
        self.last_query = None
    def execute(self, query):
        self.last_query = query
        return list(self._data)
    def explain(self, query, bind_vars=None, max_plans=1):
        self.last_query = query
        return dict(self._explain)


class DummyDB:
    def __init__(self):
        self._cols = {}
        self.aql = DummyAQL(data=[{"ok": True}], explain={"plans": ["p1"], "warnings": ["w"], "stats": {"nodes": 3}})
    def has_collection(self, name):
        return name in self._cols
    def create_collection(self, name, edge=False):
        self._cols[name] = DummySchemasCollection()
        return self._cols[name]
    def collection(self, name):
        return self._cols[name]


def test_create_schema_creates_collection_and_stores():
    db = DummyDB()
    args = {
        "name": "User",
        "collection": "users",
        "schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    }
    out = handle_create_schema(db, args)
    assert out["created"] is True
    key = "users:User"
    assert key in db.collection("mcp_schemas").docs


def test_validate_document_inline_schema_valid():
    db = DummyDB()
    args = {
        "collection": "users",
        "document": {"name": "Alice"},
        "schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    }
    out = handle_validate_document(db, args)
    assert out == {"valid": True}


def test_validate_document_stored_schema_invalid():
    db = DummyDB()
    # prepare stored schema
    handle_create_schema(db, {
        "name": "User",
        "collection": "users",
        "schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        },
    })
    # missing required field
    out = handle_validate_document(db, {
        "collection": "users",
        "document": {},
        "schema_name": "User",
    })
    assert out["valid"] is False
    assert out["errors"] and isinstance(out["errors"], list)


def test_query_builder_constructs_simple_aql_and_executes():
    db = DummyDB()
    out = handle_query_builder(db, {
        "collection": "users",
        "filters": [{"field": "age", "op": ">=", "value": 18}],
        "sort": [{"field": "age", "direction": "DESC"}],
        "limit": 5,
        "return_fields": ["name", "age"],
    })
    assert isinstance(out, list) and out and out[0].get("ok") is True
    assert "FOR doc IN users" in db.aql.last_query
    assert "FILTER doc.age >= 18" in db.aql.last_query
    assert "SORT doc.age DESC" in db.aql.last_query
    assert "LIMIT 5" in db.aql.last_query


def test_query_profile_returns_plans_and_stats():
    db = DummyDB()
    out = handle_query_profile(db, {
        "query": "FOR d IN users RETURN d",
        "bind_vars": {},
        "max_plans": 1,
    })
    assert "plans" in out and out["plans"]
    assert "stats" in out and out["stats"]
