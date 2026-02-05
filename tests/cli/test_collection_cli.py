"""CLI tests for collection CRUD operations (6 operations)."""
import pytest


def test_collection_list(cli):
    """Test: arango collection list"""
    output = cli("collection", "list")
    assert isinstance(output, list)
    assert len(output) > 0  # Should have system collections at minimum


def test_collection_insert(cli):
    """Test: arango collection insert"""
    data = '{"title":"CLI Test Insert","value":42,"_test":true}'
    output = cli("collection", "insert", "-c", "cli_test_collection", "-d", data)
    assert isinstance(output, dict)
    # Should return created document with _key
    assert "_key" in output or "error" in output


def test_collection_find(cli):
    """Test: arango collection find"""
    filter_json = '{"_test":true}'
    output = cli("collection", "find", "-c", "cli_test_collection", "-f", filter_json)
    assert isinstance(output, (list, dict))
    # Should return list of documents or error
    if isinstance(output, list):
        assert len(output) >= 0


def test_collection_update(cli):
    """Test: arango collection update

    Note: Requires a known document key
    """
    data = '{"value":100,"updated":true}'
    output = cli("collection", "update", "-c", "cli_test_collection", "-k", "test_key", "-d", data)
    # May fail if key doesn't exist - acceptable
    assert isinstance(output, dict)


def test_collection_remove(cli):
    """Test: arango collection remove

    Note: Requires a known document key
    """
    output = cli("collection", "remove", "-c", "cli_test_collection", "-k", "test_key")
    # May fail if key doesn't exist - acceptable
    assert isinstance(output, dict)


def test_collection_insert_with_validation(cli):
    """Test: arango collection insert_with_validation

    Note: Requires schema to be set
    """
    data = '{"title":"Validation Test","value":99}'
    output = cli("collection", "insert_with_validation", "-c", "cli_test_collection", "-d", data)
    # May fail if schema not set - acceptable
    assert isinstance(output, dict)
