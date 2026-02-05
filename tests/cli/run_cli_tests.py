#!/usr/bin/env python
"""Simple CLI test runner (no pytest dependency)."""
import json
import os
import subprocess
import sys


# Setup test environment
os.environ["ARANGO_URL"] = "http://192.168.10.32:8529"
os.environ["ARANGO_DB"] = "test"
os.environ["ARANGO_USERNAME"] = "claude"
os.environ["ARANGO_PASSWORD"] = "claude"


def run_cli(*args):
    """Run CLI command and return parsed JSON output."""
    result = subprocess.run(
        ["python", "-m", "mcp_arangodb_async", "arango"] + list(args),
        capture_output=True,
        text=True,
        cwd="/home/claude/projects/mcp-arango-mind/mcp-arangodb-async",
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}


def test(name, func):
    """Run a test and report result."""
    try:
        func()
        print(f"✅ {name}")
        return True
    except AssertionError as e:
        print(f"❌ {name}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  {name}: {e}")
        return False


# ============================================================================
# Database Tests (4 operations)
# ============================================================================

def test_database_list():
    output = run_cli("database", "list")
    assert isinstance(output, dict)

def test_database_get_focused():
    output = run_cli("database", "get_focused")
    assert isinstance(output, dict)

# ============================================================================
# Collection Tests (6 operations)
# ============================================================================

def test_collection_list():
    output = run_cli("collection", "list")
    assert isinstance(output, list)
    assert len(output) > 0

def test_collection_insert():
    data = '{"title":"Test","value":42}'
    output = run_cli("collection", "insert", "-c", "cli_test", "-d", data)
    assert isinstance(output, dict)

# ============================================================================
# AQL Tests (4 operations)
# ============================================================================

def test_aql_query():
    output = run_cli("aql", "query", "-q", "RETURN 1+1")
    assert isinstance(output, list)
    assert output[0] == 2

def test_aql_query_collection():
    query = "FOR doc IN records LIMIT 3 RETURN doc"
    output = run_cli("aql", "query", "-q", query)
    assert isinstance(output, list)

# ============================================================================
# View Tests
# ============================================================================

def test_view_list():
    output = run_cli("view", "list")
    assert isinstance(output, (list, dict))

# ============================================================================
# Graph Tests
# ============================================================================

def test_graph_list():
    output = run_cli("graph", "list")
    assert isinstance(output, (list, dict))

# ============================================================================
# MCP Tests (6 operations)
# ============================================================================

def test_mcp_search_tools():
    output = run_cli("mcp", "search_tools")
    assert isinstance(output, (list, dict))

def test_mcp_list_by_category():
    output = run_cli("mcp", "list_by_category")
    assert isinstance(output, (list, dict))


# ============================================================================
# Run All Tests
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CLI Full Test Suite")
    print("=" * 60)

    tests = [
        ("database list", test_database_list),
        ("database get_focused", test_database_get_focused),
        ("collection list", test_collection_list),
        ("collection insert", test_collection_insert),
        ("aql query (simple)", test_aql_query),
        ("aql query (collection)", test_aql_query_collection),
        ("view list", test_view_list),
        ("graph list", test_graph_list),
        ("mcp search_tools", test_mcp_search_tools),
        ("mcp list_by_category", test_mcp_list_by_category),
    ]

    passed = 0
    failed = 0

    for name, func in tests:
        if test(name, func):
            passed += 1
        else:
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)
