"""CLI tests for advanced view operations (5 operations)."""
import pytest


def test_view_create(cli):
    """Test: arango view create"""
    config = '{"type":"arangosearch","links":{"cli_test_nodes":{"fields":{"title":{}}}}}'
    output = cli("view", "create", "--name", "cli_temp_view", "--config", config)
    assert isinstance(output, dict)


def test_view_get(cli):
    """Test: arango view get"""
    output = cli("view", "get", "--name", "cli_test_view")
    assert isinstance(output, dict)


def test_view_update(cli):
    """Test: arango view update"""
    config = '{"links":{"cli_test_nodes":{"fields":{"value":{}}}}}'
    output = cli("view", "update", "--name", "cli_test_view", "--config", config)
    assert isinstance(output, dict)


def test_view_drop(cli):
    """Test: arango view drop"""
    output = cli("view", "drop", "--name", "cli_temp_view")
    assert isinstance(output, dict)


def test_view_search(cli):
    """Test: arango view search"""
    output = cli("view", "search", "--name", "cli_test_view", "--query", "Test")
    assert isinstance(output, (list, dict))
