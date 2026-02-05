"""CLI tests for advanced graph operations (11 operations)."""
import pytest


def test_graph_create(cli):
    """Test: arango graph create"""
    edge_def = '{"collection":"cli_temp_edges","from":["cli_test_nodes"],"to":["cli_test_nodes"]}'
    output = cli("graph", "create", "--name", "cli_temp_graph", "--edge-def", edge_def)
    assert isinstance(output, dict)


def test_graph_add_vertex_collection(cli):
    """Test: arango graph add_vertex_collection"""
    output = cli("graph", "add_vertex_collection", "--graph", "cli_test_graph", "--collection", "cli_test_nodes")
    assert isinstance(output, dict)


def test_graph_add_edge_definition(cli):
    """Test: arango graph add_edge_definition"""
    edge_def = '{"collection":"cli_test_edges","from":["cli_test_nodes"],"to":["cli_test_nodes"]}'
    output = cli("graph", "add_edge_definition", "--graph", "cli_test_graph", "--edge-def", edge_def)
    assert isinstance(output, dict)


def test_graph_add_edge(cli):
    """Test: arango graph add_edge"""
    data = '{"_from":"cli_test_nodes/node1","_to":"cli_test_nodes/node2","type":"test"}'
    output = cli("graph", "add_edge", "--graph", "cli_test_graph", "-d", data)
    assert isinstance(output, dict)


def test_graph_traverse(cli):
    """Test: arango graph traverse"""
    output = cli("graph", "traverse", "--graph", "cli_test_graph", "--start", "cli_test_nodes/node1")
    assert isinstance(output, (list, dict))


def test_graph_shortest_path(cli):
    """Test: arango graph shortest_path"""
    output = cli("graph", "shortest_path", "--graph", "cli_test_graph", "--start", "cli_test_nodes/node1", "--end", "cli_test_nodes/node3")
    assert isinstance(output, (list, dict))


def test_graph_backup(cli):
    """Test: arango graph backup"""
    output = cli("graph", "backup", "--graph", "cli_test_graph")
    assert isinstance(output, dict)


def test_graph_restore(cli):
    """Test: arango graph restore"""
    output = cli("graph", "restore", "--graph", "cli_test_graph", "--file", "backup.json")
    assert isinstance(output, dict)


def test_graph_backup_named(cli):
    """Test: arango graph backup_named"""
    output = cli("graph", "backup_named", "--graph", "cli_test_graph", "--name", "test_backup")
    assert isinstance(output, dict)


def test_graph_validate_integrity(cli):
    """Test: arango graph validate_integrity"""
    output = cli("graph", "validate_integrity", "--graph", "cli_test_graph")
    assert isinstance(output, dict)


def test_graph_statistics(cli):
    """Test: arango graph statistics"""
    output = cli("graph", "statistics", "--graph", "cli_test_graph")
    assert isinstance(output, dict)
