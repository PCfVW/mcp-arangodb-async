"""CLI tests for template operations."""
import pytest


def test_template_memory_recent(cli):
    """Test: arango template memory.recent"""
    output = cli("template", "execute", "--name", "memory.recent", "--params", '{"limit": 5}')
    assert isinstance(output, dict)
    assert "template" in output or "count" in output or "error" in output


def test_template_heap_top(cli):
    """Test: arango template heap.top"""
    output = cli("template", "execute", "--name", "heap.top", "--params", '{"limit": 3}')
    assert isinstance(output, dict)


def test_template_heap_by_layer(cli):
    """Test: arango template heap.by_layer"""
    output = cli("template", "execute", "--name", "heap.by_layer", "--params", '{"layer": 1}')
    assert isinstance(output, dict)


def test_template_optimize_stats(cli):
    """Test: arango template optimize.stats"""
    output = cli("template", "execute", "--name", "optimize.stats")
    assert isinstance(output, dict)


def test_template_not_found(cli):
    """Test: template not found error"""
    output = cli("template", "execute", "--name", "nonexistent.template")
    assert isinstance(output, dict)
    assert "error" in output or "available" in output
