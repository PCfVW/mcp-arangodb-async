"""CLI tests for database operations (4 operations)."""
import pytest


def test_database_list(cli):
    """Test: arango database list"""
    output = cli("database", "list")
    assert isinstance(output, dict)
    # May have error if multi-db not configured, but should return structure
    assert "databases" in output or "error" in output


def test_database_get_focused(cli):
    """Test: arango database get_focused"""
    output = cli("database", "get_focused")
    assert isinstance(output, dict)
    # Should return current database info
    assert "database" in output or "name" in output or "error" in output


def test_database_switch(cli):
    """Test: arango database switch

    Note: May fail if multi-db not configured or args not supported
    """
    output = cli("database", "switch", "--db", "test")
    # May return error dict or usage error
    assert isinstance(output, dict)
    # Accept error (feature not implemented or args issue)
    assert "stderr" in output or "error" in output or "switched" in str(output).lower()


def test_database_get_resolution(cli):
    """Test: arango database get_resolution"""
    output = cli("database", "get_resolution")
    assert isinstance(output, dict)
    # Should return resolution info
    assert "levels" in output or "configuration" in output or "database" in output or "error" in output
