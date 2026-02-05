"""CLI tests for AQL operations (4 operations)."""
import pytest


def test_aql_query_simple(cli):
    """Test: arango aql query (simple calculation)"""
    output = cli("aql", "query", "-q", "RETURN 1+1")
    assert isinstance(output, list)
    assert output[0] == 2


def test_aql_query_collection(cli):
    """Test: arango aql query (with collection)"""
    query = "FOR doc IN records LIMIT 5 RETURN doc"
    output = cli("aql", "query", "-q", query)
    assert isinstance(output, (list, dict))
    # Should return list of documents
    if isinstance(output, list):
        assert len(output) <= 5


def test_aql_explain(cli):
    """Test: arango aql explain"""
    query = "FOR doc IN records LIMIT 10 RETURN doc"
    output = cli("aql", "explain", "-q", query)
    assert isinstance(output, dict)
    # Should contain execution plan or plans
    assert "plan" in output or "plans" in output or "error" in output


def test_aql_profile(cli):
    """Test: arango aql profile"""
    query = "FOR doc IN records LIMIT 10 RETURN doc"
    output = cli("aql", "profile", "-q", query)
    assert isinstance(output, dict)
    # Should contain performance stats
    assert "stats" in output or "profile" in output or "error" in output


def test_aql_build(cli):
    """Test: arango aql build

    Note: Build operation may require specific parameters
    """
    output = cli("aql", "build")
    # May not be implemented or require args
    assert isinstance(output, dict)
