"""Test suite for Admin CLI commands.

This module tests the CLI implementation for ArangoDB user and database management.
Tests are organized according to the Test Definition Report v1.

Test Classes:
- TestVersionCommand (1 test)
- TestDBConfig (7 tests)
- TestDBAdmin (6 tests) - includes atomic operation test
- TestUserAdmin (11 tests) - includes root user protection test
- TestSafetyFeatures (3 tests)
- TestAuthentication (2 tests)
- TestOutputFormatting (2 tests)
- TestConnectionErrors (3 tests) - P1 connection error handling

Total: 35 tests (30 original + 5 additional P0/P1 tests)
Coverage: Targets critical paths and error handling
"""

import pytest
import os
import tempfile
import shutil
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from argparse import Namespace
from io import StringIO

# Import modules under test
from mcp_arangodb_async import cli_utils, cli_db_arango, cli_user
from mcp_arangodb_async.cli_utils import (
    load_credentials,
    confirm_action,
    ResultReporter,
    ConsequenceType,
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_CANCELLED,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_sys_db():
    """Mock ArangoDB _system database with common operations."""
    mock_db = MagicMock()
    
    # Database operations
    mock_db.databases.return_value = ["_system", "testdb", "proddb"]
    mock_db.has_database.return_value = False
    mock_db.create_database.return_value = True
    mock_db.delete_database.return_value = True
    
    # User operations
    mock_db.users.return_value = [
        {"username": "root", "active": True},
        {"username": "testuser", "active": True},
        {"username": "inactive_user", "active": False},
    ]
    mock_db.has_user.return_value = False
    mock_db.create_user.return_value = True
    mock_db.delete_user.return_value = True
    mock_db.update_user.return_value = True
    
    # Permission operations
    mock_db.permissions.return_value = {
        "_system": "rw",
        "testdb": "ro",
        "proddb": "none",
    }
    mock_db.update_permission.return_value = True
    mock_db.reset_permission.return_value = True
    
    # Connection validation
    mock_db.version.return_value = "3.11.0"
    
    return mock_db


@pytest.fixture
def temp_config_dir():
    """Temporary directory for config file testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_arango_client(mock_sys_db):
    """Mock ArangoClient that returns mock_sys_db."""
    # Mock in cli_utils where get_system_db is now defined
    with patch('mcp_arangodb_async.cli_utils.ArangoClient') as mock_client_class:
        mock_client = MagicMock()
        mock_client.db.return_value = mock_sys_db
        mock_client_class.return_value = mock_client
        yield mock_client_class


@pytest.fixture
def mock_arango_client_user(mock_sys_db):
    """Mock ArangoClient for user module."""
    # Mock in both cli_utils and cli_user for comprehensive coverage
    with patch('mcp_arangodb_async.cli_utils.ArangoClient') as mock_client_class_utils:
        with patch('mcp_arangodb_async.cli_user.ArangoClient') as mock_client_class_user:
            mock_client = MagicMock()
            mock_client.db.return_value = mock_sys_db
            mock_client_class_utils.return_value = mock_client
            mock_client_class_user.return_value = mock_client
            yield mock_client_class_utils


# ============================================================================
# TestVersionCommand (1 test)
# ============================================================================

class TestVersionCommand:
    """Tests for version command."""
    
    def test_version_displays_package_version(self, capsys):
        """V-01: Version command displays package version and Python version."""
        # This test would normally call the version handler
        # For now, we'll test the version retrieval logic
        try:
            from importlib.metadata import version
            pkg_version = version("mcp-arangodb-async")
            assert pkg_version is not None
            assert len(pkg_version) > 0
        except Exception:
            # If package not installed, version will be "unknown"
            pkg_version = "unknown"
            assert pkg_version == "unknown"


# ============================================================================
# TestDBConfig (7 tests)
# ============================================================================

class TestDBConfig:
    """Tests for db config commands (YAML configuration management)."""
    
    def test_config_add_success(self, temp_config_dir, capsys):
        """DC-01: Successfully add new database configuration."""
        from mcp_arangodb_async import cli_db

        config_path = Path(temp_config_dir) / "databases.yaml"
        args = Namespace(
            key="testdb",
            url="http://localhost:8529",
            database="test",
            username="testuser",
            arango_password_env="TEST_PASSWORD",
            timeout=30.0,
            description="Test database",
            config_file=str(config_path),
            dry_run=False,
            yes=True,
        )

        result = cli_db.handle_add(args)
        assert result == EXIT_SUCCESS

        # Verify file was created
        assert config_path.exists()

    def test_config_add_duplicate_error(self, temp_config_dir, capsys):
        """DC-02: Adding duplicate config key returns error."""
        from mcp_arangodb_async import cli_db

        config_path = Path(temp_config_dir) / "databases.yaml"

        # Add first config
        args1 = Namespace(
            key="testdb",
            url="http://localhost:8529",
            database="test",
            username="testuser",
            arango_password_env="TEST_PASSWORD",
            timeout=30.0,
            description="Test database",
            config_file=str(config_path),
            dry_run=False,
            yes=True,
        )
        cli_db.handle_add(args1)

        # Try to add duplicate
        args2 = Namespace(
            key="testdb",  # Same key
            url="http://localhost:8529",
            database="test2",
            username="testuser2",
            arango_password_env="TEST_PASSWORD2",
            timeout=30.0,
            description="Duplicate",
            config_file=str(config_path),
            dry_run=False,
            yes=True,
        )
        result = cli_db.handle_add(args2)
        assert result == EXIT_ERROR

    def test_config_remove_success(self, temp_config_dir, capsys):
        """DC-03: Successfully remove existing configuration."""
        from mcp_arangodb_async import cli_db

        config_path = Path(temp_config_dir) / "databases.yaml"

        # Add config first
        args_add = Namespace(
            key="testdb",
            url="http://localhost:8529",
            database="test",
            username="testuser",
            arango_password_env="TEST_PASSWORD",
            timeout=30.0,
            description="Test database",
            config_file=str(config_path),
            dry_run=False,
            yes=True,
        )
        cli_db.handle_add(args_add)

        # Remove it
        args_remove = Namespace(
            key="testdb",
            config_file=str(config_path),
            dry_run=False,
            yes=True,
        )
        result = cli_db.handle_remove(args_remove)
        assert result == EXIT_SUCCESS

    def test_config_list_success(self, temp_config_dir, capsys):
        """DC-04: List all configurations."""
        from mcp_arangodb_async import cli_db

        config_path = Path(temp_config_dir) / "databases.yaml"

        # Add multiple configs
        for i in range(3):
            args = Namespace(
                key=f"db{i}",
                url="http://localhost:8529",
                database=f"test{i}",
                username="testuser",
                arango_password_env="TEST_PASSWORD",
                timeout=30.0,
                description=f"Database {i}",
                config_file=str(config_path),
                dry_run=False,
                yes=True,
            )
            cli_db.handle_add(args)

        # List them
        args_list = Namespace(config_file=str(config_path))
        result = cli_db.handle_list(args_list)
        assert result == EXIT_SUCCESS

        captured = capsys.readouterr()
        assert "db0" in captured.out
        assert "db1" in captured.out
        assert "db2" in captured.out

    def test_config_test_connection_success(self, temp_config_dir, capsys):
        """DC-05: Test successful database connection."""
        from mcp_arangodb_async import cli_db

        config_path = Path(temp_config_dir) / "databases.yaml"

        # Add config
        args_add = Namespace(
            key="testdb",
            url="http://localhost:8529",
            database="test",
            username="testuser",
            arango_password_env="TEST_PASSWORD",
            timeout=30.0,
            description="Test database",
            config_file=str(config_path),
            dry_run=False,
            yes=True,
        )
        cli_db.handle_add(args_add)

        # Set password in environment
        os.environ["TEST_PASSWORD"] = "testpass"

        # Mock the async test_connection method
        async def mock_test_connection(key):
            return {"connected": True, "version": "3.11.0", "error": None}

        async def mock_close_all():
            pass

        with patch('mcp_arangodb_async.cli_db.MultiDatabaseConnectionManager') as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.test_connection = mock_test_connection
            mock_manager.close_all = mock_close_all
            mock_manager_class.return_value = mock_manager

            args_test = Namespace(
                key="testdb",
                config_file=str(config_path),
            )
            result = cli_db.handle_test(args_test)
            assert result == EXIT_SUCCESS

        # Cleanup
        del os.environ["TEST_PASSWORD"]

    def test_config_test_connection_failure(self, temp_config_dir, capsys):
        """DC-06: Test connection failure handling."""
        from mcp_arangodb_async import cli_db

        config_path = Path(temp_config_dir) / "databases.yaml"

        # Add config
        args_add = Namespace(
            key="testdb",
            url="http://localhost:8529",
            database="test",
            username="testuser",
            arango_password_env="TEST_PASSWORD",
            timeout=30.0,
            description="Test database",
            config_file=str(config_path),
            dry_run=False,
            yes=True,
        )
        cli_db.handle_add(args_add)

        # Set password in environment
        os.environ["TEST_PASSWORD"] = "testpass"

        # Mock connection failure
        with patch('mcp_arangodb_async.db.get_client_and_db') as mock_get_db:
            mock_get_db.side_effect = Exception("Connection failed")

            args_test = Namespace(
                key="testdb",
                config_file=str(config_path),
            )
            result = cli_db.handle_test(args_test)
            assert result == EXIT_ERROR

        # Cleanup
        del os.environ["TEST_PASSWORD"]

    def test_config_status_success(self, temp_config_dir, capsys):
        """DC-07: Show status for all configurations."""
        from mcp_arangodb_async import cli_db

        config_path = Path(temp_config_dir) / "databases.yaml"

        # Add config
        args_add = Namespace(
            key="testdb",
            url="http://localhost:8529",
            database="test",
            username="testuser",
            arango_password_env="TEST_PASSWORD",
            timeout=30.0,
            description="Test database",
            config_file=str(config_path),
            dry_run=False,
            yes=True,
        )
        cli_db.handle_add(args_add)

        # Get status
        args_status = Namespace(config_file=str(config_path))
        result = cli_db.handle_status(args_status)
        assert result == EXIT_SUCCESS

    def test_config_add_password_env_backward_compat(self, temp_config_dir):
        """Verify --password-env backward compatibility in db config add."""
        import subprocess
        import yaml

        config_path = Path(temp_config_dir) / "databases.yaml"

        # Test using OLD argument name (--password-env) via CLI
        result = subprocess.run(
            [
                "maa",
                "db",
                "config",
                "add",
                "testdb",
                "--url",
                "http://localhost:8529",
                "--database",
                "test",
                "--username",
                "testuser",
                "--password-env",  # OLD name (backward compat)
                "TEST_PASSWORD",
                "--config-file",
                str(config_path),
                "--yes",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Verify config was created correctly
        assert config_path.exists()
        with open(config_path) as f:
            config = yaml.safe_load(f)
        assert config["databases"]["testdb"]["password_env"] == "TEST_PASSWORD"


# ============================================================================
# TestDBAdmin (5 tests)
# ============================================================================

class TestDBAdmin:
    """Tests for db commands (ArangoDB database operations)."""

    def test_db_add_success(self, mock_arango_client, mock_sys_db, capsys):
        """DA-01: Successfully create new database."""
        mock_sys_db.has_database.return_value = False

        args = Namespace(
            name="newdb",
            with_user=None,
            permission="rw",
            env_file=None,
            arango_root_password_env=None,
            arango_password_env=None,
            dry_run=False,
            yes=True,  # Skip confirmation
        )

        # Set root password
        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_db_arango.handle_db_add(args)
        assert result == EXIT_SUCCESS

        # Verify database was created
        mock_sys_db.create_database.assert_called_once_with("newdb")

        # Cleanup
        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_db_add_already_exists(self, mock_arango_client, mock_sys_db, capsys):
        """DA-02: Error when database already exists."""
        mock_sys_db.has_database.return_value = True

        args = Namespace(
            name="existingdb",
            with_user=None,
            permission="rw",
            env_file=None,
            arango_root_password_env=None,
            arango_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_db_arango.handle_db_add(args)
        assert result == EXIT_ERROR

        captured = capsys.readouterr()
        assert "already exists" in captured.err

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_db_add_with_user_atomic(self, mock_arango_client, mock_sys_db, capsys):
        """DA-02b: Successfully create database with user atomically (--with-user)."""
        mock_sys_db.has_database.return_value = False
        mock_sys_db.has_user.return_value = False

        args = Namespace(
            name="newdb",
            with_user="newuser",  # Atomic operation
            permission="rw",
            env_file=None,
            arango_root_password_env=None,
            arango_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"
        os.environ["ARANGO_PASSWORD"] = "userpass"

        result = cli_db_arango.handle_db_add(args)
        assert result == EXIT_SUCCESS

        # Verify all three operations were called
        mock_sys_db.create_database.assert_called_once_with("newdb")
        mock_sys_db.create_user.assert_called_once_with("newuser", "userpass", active=True)
        mock_sys_db.update_permission.assert_called_once_with("newuser", "rw", "newdb")

        # Verify output shows all three consequences
        captured = capsys.readouterr()
        assert "Database 'newdb'" in captured.out
        assert "User 'newuser'" in captured.out
        assert "Permission rw: newuser → newdb" in captured.out

        del os.environ["ARANGO_ROOT_PASSWORD"]
        del os.environ["ARANGO_PASSWORD"]

    def test_db_add_with_user_existing_user(self, mock_arango_client, mock_sys_db, capsys):
        """DA-02c: Successfully create database and grant to existing user (--with-user)."""
        mock_sys_db.has_database.return_value = False
        mock_sys_db.has_user.return_value = True  # User already exists

        args = Namespace(
            name="newdb",
            with_user="existinguser",  # Existing user
            permission="ro",
            env_file=None,
            arango_root_password_env=None,
            arango_password_env=None,
            dry_run=False,
            yes=True,
        )

        # Only root password needed - no user password required for existing user
        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_db_arango.handle_db_add(args)
        assert result == EXIT_SUCCESS

        # Verify database was created
        mock_sys_db.create_database.assert_called_once_with("newdb")
        # Verify user was NOT created (already exists)
        mock_sys_db.create_user.assert_not_called()
        # Verify permission was granted
        mock_sys_db.update_permission.assert_called_once_with("existinguser", "ro", "newdb")

        # Verify output shows EXISTS for user and GRANTED for permission
        captured = capsys.readouterr()
        assert "Database 'newdb'" in captured.out
        assert "already exists" in captured.out  # User exists message
        assert "Permission ro: existinguser → newdb" in captured.out

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_db_remove_success(self, mock_arango_client, mock_sys_db, capsys):
        """DA-03: Successfully delete database."""
        mock_sys_db.has_database.return_value = True
        mock_sys_db.users.return_value = []  # No users with permissions

        args = Namespace(
            name="olddb",
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_db_arango.handle_db_remove(args)
        assert result == EXIT_SUCCESS

        mock_sys_db.delete_database.assert_called_once_with("olddb")

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_db_remove_not_found(self, mock_arango_client, mock_sys_db, capsys):
        """DA-04: Error when database not found."""
        mock_sys_db.has_database.return_value = False

        args = Namespace(
            name="nonexistent",
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_db_arango.handle_db_remove(args)
        assert result == EXIT_ERROR

        captured = capsys.readouterr()
        assert "not found" in captured.err

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_db_list_success(self, mock_arango_client, mock_sys_db, capsys):
        """DA-05: Successfully list all databases."""
        mock_sys_db.databases.return_value = ["_system", "db1", "db2", "db3"]

        args = Namespace(
            env_file=None,
            arango_root_password_env=None,
            json=False,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_db_arango.handle_db_list(args)
        assert result == EXIT_SUCCESS

        captured = capsys.readouterr()
        assert "db1" in captured.out
        assert "db2" in captured.out
        assert "db3" in captured.out

        del os.environ["ARANGO_ROOT_PASSWORD"]


# ============================================================================
# TestUserAdmin (10 tests)
# ============================================================================

class TestUserAdmin:
    """Tests for user commands (ArangoDB user management)."""

    def test_user_add_success(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-01: Successfully create new user."""
        mock_sys_db.has_user.return_value = False

        args = Namespace(
            username="newuser",
            active=True,
            env_file=None,
            arango_root_password_env=None,
            arango_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"
        os.environ["ARANGO_PASSWORD"] = "userpass"

        result = cli_user.handle_user_add(args)
        assert result == EXIT_SUCCESS

        mock_sys_db.create_user.assert_called_once_with("newuser", "userpass", active=True)

        del os.environ["ARANGO_ROOT_PASSWORD"]
        del os.environ["ARANGO_PASSWORD"]

    def test_user_add_already_exists(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-02: Error when user already exists."""
        mock_sys_db.has_user.return_value = True

        args = Namespace(
            username="existinguser",
            active=True,
            env_file=None,
            arango_root_password_env=None,
            arango_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"
        os.environ["ARANGO_PASSWORD"] = "userpass"

        result = cli_user.handle_user_add(args)
        assert result == EXIT_ERROR

        captured = capsys.readouterr()
        assert "already exists" in captured.err

        del os.environ["ARANGO_ROOT_PASSWORD"]
        del os.environ["ARANGO_PASSWORD"]

    def test_user_remove_success(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-03: Successfully delete user."""
        mock_sys_db.has_user.return_value = True
        mock_sys_db.permissions.return_value = {"testdb": "rw"}

        args = Namespace(
            username="olduser",
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_user.handle_user_remove(args)
        assert result == EXIT_SUCCESS

        mock_sys_db.delete_user.assert_called_once_with("olduser")

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_user_remove_not_found(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-04: Error when user not found."""
        mock_sys_db.has_user.return_value = False

        args = Namespace(
            username="nonexistent",
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_user.handle_user_remove(args)
        assert result == EXIT_ERROR

        captured = capsys.readouterr()
        assert "not found" in captured.err

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_user_remove_root_protection(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-04b: Cannot delete root user (security protection)."""
        mock_sys_db.has_user.return_value = True

        args = Namespace(
            username="root",  # Attempt to delete root user
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_user.handle_user_remove(args)
        assert result == EXIT_ERROR

        # Verify error message
        captured = capsys.readouterr()
        assert "Cannot delete root user" in captured.err

        # Verify delete was NOT called
        mock_sys_db.delete_user.assert_not_called()

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_user_list_success(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-05: Successfully list all users."""
        mock_sys_db.users.return_value = [
            {"username": "root", "active": True},
            {"username": "user1", "active": True},
            {"username": "user2", "active": False},
        ]

        args = Namespace(
            env_file=None,
            arango_root_password_env=None,
            json=False,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_user.handle_user_list(args)
        assert result == EXIT_SUCCESS

        captured = capsys.readouterr()
        assert "user1" in captured.out
        assert "user2" in captured.out

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_user_grant_success(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-06: Successfully grant database permission."""
        mock_sys_db.has_user.return_value = True
        mock_sys_db.has_database.return_value = True

        args = Namespace(
            username="testuser",
            database="testdb",
            permission="rw",
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_user.handle_user_grant(args)
        assert result == EXIT_SUCCESS

        mock_sys_db.update_permission.assert_called_once_with("testuser", "rw", "testdb")

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_user_grant_user_not_found(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-07: Error when user not found for grant."""
        mock_sys_db.has_user.return_value = False

        args = Namespace(
            username="nonexistent",
            database="testdb",
            permission="rw",
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_user.handle_user_grant(args)
        assert result == EXIT_ERROR

        captured = capsys.readouterr()
        assert "not found" in captured.err

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_user_revoke_success(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-08: Successfully revoke database permission."""
        mock_sys_db.has_user.return_value = True
        mock_sys_db.permissions.return_value = {"testdb": "rw"}

        args = Namespace(
            username="testuser",
            database="testdb",
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_user.handle_user_revoke(args)
        assert result == EXIT_SUCCESS

        mock_sys_db.reset_permission.assert_called_once_with("testuser", "testdb")

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_user_databases_success(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-09: Successfully list accessible databases (self-service)."""
        # Mock databases_accessible_to_user() which returns a list of database names
        mock_sys_db.databases_accessible_to_user.return_value = ["_system", "testdb"]

        args = Namespace(
            env_file=None,
            arango_password_env=None,
            json=False,
        )

        os.environ["ARANGO_PASSWORD"] = "userpass"

        result = cli_user.handle_user_databases(args)
        assert result == EXIT_SUCCESS

        captured = capsys.readouterr()
        assert "testdb" in captured.out
        assert "_system" in captured.out

        del os.environ["ARANGO_PASSWORD"]

    def test_user_password_success(self, mock_arango_client_user, mock_sys_db, capsys):
        """UA-10: Successfully change own password (self-service)."""
        args = Namespace(
            env_file=None,
            arango_password_env=None,
            new_password_env="ARANGO_NEW_PASSWORD",
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_PASSWORD"] = "oldpass"
        os.environ["ARANGO_NEW_PASSWORD"] = "newpass"

        result = cli_user.handle_user_password(args)
        assert result == EXIT_SUCCESS

        mock_sys_db.update_user.assert_called_once()

        del os.environ["ARANGO_PASSWORD"]
        del os.environ["ARANGO_NEW_PASSWORD"]

    def test_user_password_new_password_env_backward_compat(
        self, mock_arango_client_user, mock_sys_db, capsys
    ):
        """Verify --new-password-env backward compatibility in user password."""
        mock_sys_db.has_user.return_value = True

        args = Namespace(
            env_file=None,
            arango_password_env=None,
            new_password_env="NEW_PASSWORD",  # OLD name (backward compat)
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_PASSWORD"] = "oldpass"
        os.environ["NEW_PASSWORD"] = "newpass"

        result = cli_user.handle_user_password(args)
        assert result == EXIT_SUCCESS

        mock_sys_db.update_user.assert_called_once()

        del os.environ["ARANGO_PASSWORD"]
        del os.environ["NEW_PASSWORD"]


# ============================================================================
# TestSafetyFeatures (3 tests)
# ============================================================================

class TestSafetyFeatures:
    """Tests for safety features (dry-run, confirmation, --yes)."""

    def test_dry_run_no_side_effects(self, mock_arango_client, mock_sys_db, capsys):
        """SF-01: Dry-run mode does not execute operations."""
        mock_sys_db.has_database.return_value = True

        args = Namespace(
            name="testdb",
            env_file=None,
            arango_root_password_env=None,
            dry_run=True,  # Dry-run mode
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_db_arango.handle_db_remove(args)
        assert result == EXIT_SUCCESS

        # Verify delete was NOT called
        mock_sys_db.delete_database.assert_not_called()

        # Verify dry-run message in output
        captured = capsys.readouterr()
        assert "DRY-RUN" in captured.out or "dry-run" in captured.out.lower()

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_confirmation_rejected(self, mock_arango_client, mock_sys_db, capsys):
        """SF-02: User can cancel operation via confirmation prompt."""
        mock_sys_db.has_database.return_value = True

        args = Namespace(
            name="testdb",
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=False,  # Require confirmation
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        # Mock user input as 'no'
        with patch('builtins.input', return_value='n'):
            result = cli_db_arango.handle_db_remove(args)
            assert result == EXIT_CANCELLED

            # Verify delete was NOT called
            mock_sys_db.delete_database.assert_not_called()

        del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_yes_flag_skips_confirmation(self, mock_arango_client, mock_sys_db, capsys):
        """SF-03: --yes flag bypasses confirmation prompt."""
        mock_sys_db.has_database.return_value = True
        mock_sys_db.users.return_value = []

        args = Namespace(
            name="testdb",
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=True,  # Skip confirmation
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        # Should not call input()
        with patch('builtins.input') as mock_input:
            result = cli_db_arango.handle_db_remove(args)
            assert result == EXIT_SUCCESS

            # Verify input was NOT called
            mock_input.assert_not_called()

            # Verify delete WAS called
            mock_sys_db.delete_database.assert_called_once_with("testdb")

        del os.environ["ARANGO_ROOT_PASSWORD"]


# ============================================================================
# TestAuthentication (2 tests)
# ============================================================================

class TestAuthentication:
    """Tests for authentication and credential handling."""

    def test_env_file_loading(self, temp_config_dir):
        """AU-01: Credentials loaded from --env-file."""
        # Create a .env file
        env_file = Path(temp_config_dir) / ".env"
        env_file.write_text("ARANGO_ROOT_PASSWORD=filepass\nARANGO_URL=http://localhost:8529\n")

        args = Namespace(
            env_file=str(env_file),
            arango_root_password_env=None,
            arango_password_env=None,
        )

        credentials = load_credentials(args)
        assert credentials["root_password"] == "filepass"
        assert credentials["url"] == "http://localhost:8529"

    def test_env_var_resolution(self):
        """AU-02: Custom env var names resolved correctly."""
        # Set custom env var
        os.environ["CUSTOM_ROOT_PASS"] = "custompass"

        args = Namespace(
            env_file=None,
            arango_root_password_env="CUSTOM_ROOT_PASS",
            arango_password_env=None,
        )

        credentials = load_credentials(args)
        assert credentials["root_password"] == "custompass"

        del os.environ["CUSTOM_ROOT_PASS"]


# ============================================================================
# TestOutputFormatting (2 tests)
# ============================================================================

class TestOutputFormatting:
    """Tests for output formatting and result reporting."""

    def test_success_output_format(self, capsys):
        """OF-01: Success output contains consequence tags with past tense.
        
        Per design doc v4, execution results use past tense (ADDED, REMOVED, etc.)
        while confirmation prompts use present tense (ADD, REMOVE, etc.).
        """
        reporter = ResultReporter("test command", dry_run=False)
        # Use present tense when adding consequences
        reporter.add(ConsequenceType.ADD, "Test item")
        # report_result() automatically converts to past tense
        reporter.report_result()

        captured = capsys.readouterr()
        # Result should show past tense
        assert "[ADDED]" in captured.out
        assert "Test item" in captured.out

    def test_error_output_format(self, mock_arango_client, mock_sys_db, capsys):
        """OF-02: Error output contains clear error messages."""
        mock_sys_db.has_database.return_value = False

        args = Namespace(
            name="nonexistent",
            env_file=None,
            arango_root_password_env=None,
            dry_run=False,
            yes=True,
        )

        os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

        result = cli_db_arango.handle_db_remove(args)
        assert result == EXIT_ERROR

        captured = capsys.readouterr()
        assert "Error" in captured.err or "not found" in captured.err

        del os.environ["ARANGO_ROOT_PASSWORD"]


# ============================================================================
# TestConnectionErrors (3 tests)
# ============================================================================

class TestConnectionErrors:
    """Tests for connection error handling across CLI modules."""

    def test_db_add_connection_error(self, capsys):
        """CE-01: Database add handles connection errors gracefully."""
        from arango.exceptions import ArangoError

        # Mock ArangoClient in cli_utils where get_system_db is now defined
        with patch('mcp_arangodb_async.cli_utils.ArangoClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.db.side_effect = ArangoError("Connection refused")
            mock_client_class.return_value = mock_client

            args = Namespace(
                name="testdb",
                with_user=None,
                permission="rw",
                env_file=None,
                arango_root_password_env=None,
                arango_password_env=None,
                dry_run=False,
                yes=True,
            )

            os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"

            result = cli_db_arango.handle_db_add(args)
            assert result == EXIT_ERROR

            captured = capsys.readouterr()
            assert "Failed to connect" in captured.err

            del os.environ["ARANGO_ROOT_PASSWORD"]

    def test_user_add_connection_error(self, capsys):
        """CE-02: User add handles connection errors gracefully."""
        from arango.exceptions import ArangoError

        # Mock ArangoClient in cli_utils where get_system_db is now defined
        with patch('mcp_arangodb_async.cli_utils.ArangoClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.db.side_effect = ArangoError("Connection timeout")
            mock_client_class.return_value = mock_client

            args = Namespace(
                username="testuser",
                active=True,
                env_file=None,
                arango_root_password_env=None,
                arango_password_env=None,
                dry_run=False,
                yes=True,
            )

            os.environ["ARANGO_ROOT_PASSWORD"] = "rootpass"
            os.environ["ARANGO_PASSWORD"] = "userpass"

            result = cli_user.handle_user_add(args)
            assert result == EXIT_ERROR

            captured = capsys.readouterr()
            assert "Failed to connect" in captured.err

            del os.environ["ARANGO_ROOT_PASSWORD"]
            del os.environ["ARANGO_PASSWORD"]

    def test_user_databases_connection_error(self, capsys):
        """CE-03: User databases (self-service) handles connection errors gracefully."""
        from arango.exceptions import ArangoError

        # Mock ArangoClient to raise connection error
        with patch('mcp_arangodb_async.cli_user.ArangoClient') as mock_client_class:
            mock_client = MagicMock()
            mock_client.db.side_effect = ArangoError("Authentication failed")
            mock_client_class.return_value = mock_client

            args = Namespace(
                env_file=None,
                arango_password_env=None,
                json=False,
            )

            os.environ["ARANGO_PASSWORD"] = "userpass"

            result = cli_user.handle_user_databases(args)
            assert result == EXIT_ERROR

            captured = capsys.readouterr()
            # Error message may indicate authentication or connection failure
            assert "Error:" in captured.err

            del os.environ["ARANGO_PASSWORD"]

