"""Shared fixtures for CLI tests."""
import json
import os
import subprocess
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Setup test database environment variables."""
    os.environ["ARANGO_URL"] = "http://192.168.10.32:8529"
    os.environ["ARANGO_DB"] = "test"
    os.environ["ARANGO_USERNAME"] = "claude"
    os.environ["ARANGO_PASSWORD"] = "claude"


def run_cli(*args):
    """Run CLI command and return parsed JSON output.

    Args:
        *args: CLI arguments (e.g., "database", "list")

    Returns:
        Parsed JSON output or raw text if not JSON

    Raises:
        AssertionError: If CLI returns non-zero exit code
    """
    result = subprocess.run(
        ["python", "-m", "mcp_arangodb_async", "arango"] + list(args),
        capture_output=True,
        text=True,
        cwd="/home/claude/projects/mcp-arango-mind/mcp-arangodb-async",
    )

    # Try to parse as JSON
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        # Return raw output if not JSON
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}


@pytest.fixture
def cli():
    """Fixture that provides CLI runner function."""
    return run_cli
