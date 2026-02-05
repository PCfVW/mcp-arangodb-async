#!/usr/bin/env python
"""Setup test data from JSON file."""
import json
import os
from mcp_arangodb_async.utility.db import get_client_and_db
from mcp_arangodb_async.utility.config import load_config

# Setup environment
os.environ["ARANGO_URL"] = "http://192.168.10.32:8529"
os.environ["ARANGO_DB"] = "test"
os.environ["ARANGO_USERNAME"] = "claude"
os.environ["ARANGO_PASSWORD"] = "claude"

cfg = load_config()
client, db = get_client_and_db(cfg)

# Load test data
with open("tests/cli/test_data.json") as f:
    data = json.load(f)

print("Setting up test data...")

# Create collections
for coll_spec in data["collections"]:
    name = coll_spec["name"]
    edge = coll_spec["type"] == "edge"
    if not db.has_collection(name):
        db.create_collection(name, edge=edge)
        print(f"✅ Created collection: {name}")
    else:
        print(f"⏭️  Collection exists: {name}")

# Insert documents
for coll_name, docs in data["documents"].items():
    coll = db.collection(coll_name)
    for doc in docs:
        try:
            coll.insert(doc, overwrite=True)
        except:
            pass
    print(f"✅ Inserted {len(docs)} docs into {coll_name}")

# Create graphs
for graph_spec in data["graphs"]:
    name = graph_spec["name"]
    if not db.has_graph(name):
        db.create_graph(
            name,
            edge_definitions=graph_spec["edgeDefinitions"]
        )
        print(f"✅ Created graph: {name}")
    else:
        print(f"⏭️  Graph exists: {name}")

# Create views
for view_spec in data["views"]:
    name = view_spec["name"]
    if name not in [v["name"] for v in db.views()]:
        db.create_view(name, view_spec["type"], view_spec.get("properties", {}))
        print(f"✅ Created view: {name}")
    else:
        print(f"⏭️  View exists: {name}")

print("\n✅ Test data setup complete!")
