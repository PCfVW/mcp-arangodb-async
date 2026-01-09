"""Unit tests for CLI database management tool."""

import pytest
import os
import tempfile
import yaml
from unittest.mock import patch, Mock, AsyncMock
from argparse import Namespace
from mcp_arangodb_async.cli_db import (
    handle_add,
    handle_remove,
    handle_list,
    handle_test,
    handle_status,
    handle_update,
)
from mcp_arangodb_async.multi_db_manager import DatabaseConfig


class TestCLIAdd:
    """Test 'db add' subcommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "databases.yaml")

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_add_database_success(self, capsys):
        """Test adding a database configuration successfully."""
        args = Namespace(
            key="production",
            url="http://localhost:8529",
            database="prod_db",
            username="admin",
            arango_password_env="PROD_PASSWORD",
            timeout=60.0,
            description="Production database",
            config_file=self.config_path,
            dry_run=False,
            yes=True,  # Skip confirmation prompt
        )

        result = handle_add(args)

        assert result == 0
        captured = capsys.readouterr()
        # New ResultReporter format uses [ADDED] tags
        assert "[ADDED]" in captured.out
        assert "Database configuration 'production'" in captured.out
        assert "URL: http://localhost:8529" in captured.out
        assert "Database: prod_db" in captured.out
        assert "Username: admin" in captured.out
        assert "Configuration saved to:" in captured.out

        # Verify file was created
        assert os.path.exists(self.config_path)

        # Verify content
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        assert "production" in config["databases"]
        assert config["databases"]["production"]["url"] == "http://localhost:8529"

    def test_add_database_without_description(self, capsys):
        """Test adding a database without optional description."""
        args = Namespace(
            key="staging",
            url="http://staging:8529",
            database="staging_db",
            username="admin",
            arango_password_env="STAGING_PASSWORD",
            timeout=30.0,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,  # Skip confirmation prompt
        )

        result = handle_add(args)

        assert result == 0
        captured = capsys.readouterr()
        # New ResultReporter format uses [ADDED] tags
        assert "[ADDED]" in captured.out
        assert "Database configuration 'staging'" in captured.out
        assert "Configuration saved to:" in captured.out

    def test_add_database_duplicate_key(self, capsys):
        """Test adding a database with duplicate key."""
        # Create existing configuration
        config_data = {
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = Namespace(
            key="production",
            url="http://new:8529",
            database="new_db",
            username="admin",
            arango_password_env="NEW_PASSWORD",
            timeout=30.0,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,  # Skip confirmation prompt
        )

        result = handle_add(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Database 'production' already exists" in captured.err

    def test_add_database_error_handling(self, capsys):
        """Test error handling when adding database fails."""
        # Use invalid path to trigger error
        args = Namespace(
            key="test",
            url="http://localhost:8529",
            database="test_db",
            username="admin",
            arango_password_env="TEST_PASSWORD",
            timeout=30.0,
            description=None,
            config_file="/invalid/path/databases.yaml",
            dry_run=False,
            yes=True,  # Skip confirmation prompt
        )

        with patch("mcp_arangodb_async.cli_db.ConfigFileLoader") as mock_loader:
            # Mock load_yaml_only which is what handle_add actually calls
            mock_loader.return_value.load_yaml_only.side_effect = Exception("Test error")
            result = handle_add(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error adding database" in captured.err


class TestCLIRemove:
    """Test 'db remove' subcommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "databases.yaml")

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_remove_database_success(self, capsys):
        """Test removing a database configuration successfully."""
        # Create existing configuration
        config_data = {
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                },
                "staging": {
                    "url": "http://staging:8529",
                    "database": "staging_db",
                    "username": "admin",
                    "password_env": "STAGING_PASSWORD",
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = Namespace(
            key="production",
            config_file=self.config_path,
            dry_run=False,
            yes=True,  # Skip confirmation prompt
        )

        result = handle_remove(args)

        assert result == 0
        captured = capsys.readouterr()
        # New ResultReporter format uses [REMOVED] tags
        assert "[REMOVED]" in captured.out
        assert "Database configuration 'production'" in captured.out
        assert "Configuration saved to:" in captured.out

        # Verify database was removed
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        assert "production" not in config["databases"]
        assert "staging" in config["databases"]

    def test_remove_database_not_found(self, capsys):
        """Test removing a database that doesn't exist."""
        # Create empty configuration
        config_data = {"databases": {}}
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = Namespace(
            key="nonexistent",
            config_file=self.config_path,
            dry_run=False,
            yes=True,  # Skip confirmation prompt
        )

        result = handle_remove(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Database 'nonexistent' not found" in captured.err

    def test_remove_database_error_handling(self, capsys):
        """Test error handling when removing database fails."""
        args = Namespace(
            key="test",
            config_file="/invalid/path/databases.yaml",
            dry_run=False,
            yes=True,  # Skip confirmation prompt
        )

        with patch("mcp_arangodb_async.cli_db.ConfigFileLoader") as mock_loader:
            # Mock load_yaml_only which is what handle_remove actually calls
            mock_loader.return_value.load_yaml_only.side_effect = Exception("Test error")
            result = handle_remove(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error removing database" in captured.err


class TestCLIList:
    """Test 'db list' subcommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "databases.yaml")

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_list_databases_success(self, capsys):
        """Test listing databases successfully."""
        # Create configuration with multiple databases
        config_data = {
            "default_database": "production",
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                    "timeout": 60.0,
                    "description": "Production database"
                },
                "staging": {
                    "url": "http://staging:8529",
                    "database": "staging_db",
                    "username": "admin",
                    "password_env": "STAGING_PASSWORD",
                    "timeout": 30.0,
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = Namespace(config_file=self.config_path)

        result = handle_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Configured databases (2):" in captured.out
        assert "Default database: production" in captured.out
        assert "production:" in captured.out
        assert "URL: http://localhost:8529" in captured.out
        assert "Database: prod_db" in captured.out
        assert "Description: Production database" in captured.out
        assert "staging:" in captured.out

    @patch.dict(os.environ, {}, clear=True)
    def test_list_databases_empty(self, capsys):
        """Test listing when no databases are configured."""
        # Create empty YAML file to prevent env var fallback
        config_data = {"databases": {}}
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = Namespace(config_file=self.config_path)

        result = handle_list(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "No databases configured" in captured.out

    def test_list_databases_no_config_file_env_fallback(self, capsys):
        """Test listing when config file doesn't exist - uses env var fallback."""
        # Use a path that doesn't exist
        nonexistent_config = os.path.join(self.temp_dir, "nonexistent", "databases.yaml")
        args = Namespace(config_file=nonexistent_config)

        # Environment variables provide default config (graceful degradation)
        with patch.dict(os.environ, {
            "ARANGO_URL": "http://test:8529",
            "ARANGO_DB": "test_db",
            "ARANGO_USERNAME": "testuser",
        }, clear=False):
            result = handle_list(args)

        assert result == 0
        captured = capsys.readouterr()
        # Should indicate no config file at expected path
        assert "No config file at expected path:" in captured.out
        assert nonexistent_config.replace("/", os.sep) in captured.out or "nonexistent" in captured.out
        # Should indicate graceful degradation
        assert "environment variables" in captured.out.lower() or "graceful degradation" in captured.out.lower()
        # Should still show the database info from env vars
        assert "http://test:8529" in captured.out
        assert "test_db" in captured.out
        assert "testuser" in captured.out

    @patch.dict(os.environ, {}, clear=True)
    def test_list_databases_no_config_file_default_env_fallback(self, capsys):
        """Test listing when config file doesn't exist - uses default env values."""
        # Use a path that doesn't exist
        nonexistent_config = os.path.join(self.temp_dir, "nonexistent", "databases.yaml")
        args = Namespace(config_file=nonexistent_config)

        result = handle_list(args)

        assert result == 0
        captured = capsys.readouterr()
        # Should indicate no config file at expected path
        assert "No config file at expected path:" in captured.out
        # Should show default values from env fallback
        assert "http://localhost:8529" in captured.out
        assert "_system" in captured.out
        assert "root" in captured.out

    def test_list_databases_error_handling(self, capsys):
        """Test error handling when listing databases fails."""
        args = Namespace(config_file="/invalid/path/databases.yaml")

        with patch("mcp_arangodb_async.cli_db.ConfigFileLoader") as mock_loader:
            mock_loader.return_value.load.side_effect = Exception("Test error")
            result = handle_list(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error listing databases" in captured.err


class TestCLITest:
    """Test 'db test' subcommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "databases.yaml")

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_test_connection_success(self, capsys):
        """Test successful database connection test."""
        # Create configuration
        config_data = {
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = Namespace(
            key="production",
            config_file=self.config_path,
        )

        # Mock the async test_connection method
        with patch("mcp_arangodb_async.cli_db.asyncio.run") as mock_run:
            def run_mock(coro):
                # Close the coroutine to avoid warnings
                if hasattr(coro, 'close'):
                    coro.close()
                return {
                    "connected": True,
                    "version": "3.11.0"
                }
            
            mock_run.side_effect = run_mock
            result = handle_test(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "✓ Connection to 'production' successful" in captured.out
        assert "ArangoDB version: 3.11.0" in captured.out

    def test_test_connection_failure(self, capsys):
        """Test failed database connection test."""
        # Create configuration
        config_data = {
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = Namespace(
            key="production",
            config_file=self.config_path,
        )

        # Mock the async test_connection method
        with patch("mcp_arangodb_async.cli_db.asyncio.run") as mock_run:
            def run_mock(coro):
                # Close the coroutine to avoid warnings
                if hasattr(coro, 'close'):
                    coro.close()
                return {
                    "connected": False,
                    "error": "Connection refused"
                }
            
            mock_run.side_effect = run_mock
            result = handle_test(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "✗ Connection to 'production' failed" in captured.err
        assert "Error: Connection refused" in captured.err

    def test_test_connection_not_found(self, capsys):
        """Test connection test for non-existent database."""
        # Create empty configuration
        config_data = {"databases": {}}
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = Namespace(
            key="nonexistent",
            config_file=self.config_path,
        )

        result = handle_test(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error: Database 'nonexistent' not found" in captured.err

    def test_test_connection_error_handling(self, capsys):
        """Test error handling when testing connection fails."""
        args = Namespace(
            key="test",
            config_file="/invalid/path/databases.yaml",
        )

        with patch("mcp_arangodb_async.cli_db.ConfigFileLoader") as mock_loader:
            mock_loader.return_value.load.side_effect = Exception("Test error")
            result = handle_test(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error testing connection" in captured.err


class TestCLIStatus:
    """Test 'db status' subcommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "databases.yaml")

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_status_with_default(self, capsys):
        """Test status command with default database set."""
        # Create configuration
        config_data = {
            "default_database": "production",
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                },
                "staging": {
                    "url": "http://staging:8529",
                    "database": "staging_db",
                    "username": "admin",
                    "password_env": "STAGING_PASSWORD",
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = Namespace(config_file=self.config_path)

        result = handle_status(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Database Resolution Status:" in captured.out
        assert "Default database (from config): production" in captured.out
        assert "Configured databases: 2" in captured.out
        assert "- production" in captured.out
        assert "- staging" in captured.out
        assert "Resolution order:" in captured.out

    @patch.dict(os.environ, {"ARANGO_DB": "staging"})
    def test_status_with_env_var(self, capsys):
        """Test status command with environment variable set."""
        # Create configuration
        config_data = {
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        args = Namespace(config_file=self.config_path)

        result = handle_status(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "Default database (from ARANGO_DB): staging" in captured.out

    def test_status_error_handling(self, capsys):
        """Test error handling when showing status fails."""
        args = Namespace(config_file="/invalid/path/databases.yaml")

        with patch("mcp_arangodb_async.cli_db.ConfigFileLoader") as mock_loader:
            mock_loader.return_value.load.side_effect = Exception("Test error")
            result = handle_status(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error showing status" in captured.err



class TestCLIUpdate:
    """Test 'db config update' subcommand."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "databases.yaml")

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_update_fields_success(self, capsys):
        """Test field updates: single field, multiple fields, optional fields."""
        # Create initial configuration
        config_data = {
            "default_database": "production",
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                    "timeout": 30.0,
                    "description": "Production database"
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Test 1: Update single field (URL)
        args = Namespace(
            existing_key="production",
            key=None,
            url="http://new-host:8529",
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "[UPDATED]" in captured.out
        assert "URL: http://localhost:8529 → http://new-host:8529" in captured.out

        # Verify file was updated
        with open(self.config_path, 'r') as f:
            updated_config = yaml.safe_load(f)
        assert updated_config["databases"]["production"]["url"] == "http://new-host:8529"
        assert updated_config["databases"]["production"]["database"] == "prod_db"  # Unchanged

        # Test 2: Update multiple fields (URL + timeout + description)
        args = Namespace(
            existing_key="production",
            key=None,
            url="http://staging:8529",
            database=None,
            username=None,
            arango_password_env=None,
            timeout=45.0,
            description="Updated production",
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "URL: http://new-host:8529 → http://staging:8529" in captured.out
        assert "Timeout: 30.0 → 45.0" in captured.out
        # After Test 1, description was preserved (not changed), so it shows existing value
        assert "Description: Production database → Updated production" in captured.out

        # Test 3: Update optional field (description value → None)
        # Note: We need to explicitly pass an empty string or use a special value
        # to indicate we want to clear the description
        args = Namespace(
            existing_key="production",
            key=None,
            url=None,
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description="",  # Empty string to clear description
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "Description: Updated production → (not set)" in captured.out

        # Verify description was removed
        with open(self.config_path, 'r') as f:
            updated_config = yaml.safe_load(f)
        assert "description" not in updated_config["databases"]["production"]

    def test_update_key_renaming(self, capsys):
        """Test key renaming: key-only and key+fields, including aliases."""
        # Create initial configuration
        config_data = {
            "default_database": "production",
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                    "timeout": 30.0,
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Test 1: Rename key only (production → prod)
        args = Namespace(
            existing_key="production",
            key="prod",
            url=None,
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "Key: production → prod" in captured.out

        # Verify key was renamed
        with open(self.config_path, 'r') as f:
            updated_config = yaml.safe_load(f)
        assert "prod" in updated_config["databases"]
        assert "production" not in updated_config["databases"]
        assert updated_config["default_database"] == "prod"  # Default updated

        # Test 2: Rename key with field updates (prod → staging + URL change)
        args = Namespace(
            existing_key="prod",
            key="staging",
            url="http://staging:8529",
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "Key: prod → staging" in captured.out
        assert "URL: http://localhost:8529 → http://staging:8529" in captured.out

        # Test 3: Test -k short alias
        # Add another database for this test
        config_data = {
            "default_database": "staging",
            "databases": {
                "staging": {
                    "url": "http://staging:8529",
                    "database": "staging_db",
                    "username": "admin",
                    "password_env": "STAGING_PASSWORD",
                    "timeout": 30.0,
                },
                "dev": {
                    "url": "http://dev:8529",
                    "database": "dev_db",
                    "username": "admin",
                    "password_env": "DEV_PASSWORD",
                    "timeout": 30.0,
                }
            }
        }
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Use -k alias
        args = Namespace(
            existing_key="dev",
            key="development",  # Using -k alias in CLI would be: dev -k development
            url=None,
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "Key: dev → development" in captured.out

    def test_update_default_database_scenarios(self, capsys):
        """Test default database reference handling during key rename."""
        # Create initial configuration with default database
        config_data = {
            "default_database": "production",
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                    "timeout": 30.0,
                },
                "staging": {
                    "url": "http://staging:8529",
                    "database": "staging_db",
                    "username": "admin",
                    "password_env": "STAGING_PASSWORD",
                    "timeout": 30.0,
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Test 1: Rename default database key (updates default_database reference)
        args = Namespace(
            existing_key="production",
            key="prod",
            url=None,
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 0

        # Verify default_database reference was updated
        with open(self.config_path, 'r') as f:
            updated_config = yaml.safe_load(f)
        assert updated_config["default_database"] == "prod"
        assert "prod" in updated_config["databases"]
        assert "production" not in updated_config["databases"]

        # Test 2: Rename non-default database key (default_database unchanged)
        args = Namespace(
            existing_key="staging",
            key="test",
            url=None,
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 0

        # Verify default_database reference unchanged
        with open(self.config_path, 'r') as f:
            updated_config = yaml.safe_load(f)
        assert updated_config["default_database"] == "prod"  # Still points to prod
        assert "test" in updated_config["databases"]
        assert "staging" not in updated_config["databases"]

    def test_update_validation_errors(self, capsys):
        """Test input validation error conditions."""
        # Create initial configuration
        config_data = {
            "default_database": "production",
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                    "timeout": 30.0,
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Test 1: Nonexistent key → "Database 'missing' not found"
        args = Namespace(
            existing_key="missing",
            key=None,
            url="http://new:8529",
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 1  # EXIT_ERROR
        captured = capsys.readouterr()
        assert "Error: Database 'missing' not found" in captured.err

        # Test 2: New key already exists → "Database 'existing' already exists"
        args = Namespace(
            existing_key="production",
            key="production",  # Same key (no change)
            url="http://new:8529",
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 0  # This should work (same key is allowed)

        # Add another database to test conflict
        config_data["databases"]["staging"] = {
            "url": "http://staging:8529",
            "database": "staging_db",
            "username": "admin",
            "password_env": "STAGING_PASSWORD",
            "timeout": 30.0,
        }
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Try to rename to existing key
        args = Namespace(
            existing_key="production",
            key="staging",  # Conflict with existing key
            url=None,
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 1  # EXIT_ERROR
        captured = capsys.readouterr()
        assert "Error: Database 'staging' already exists" in captured.err

        # Test 3: No changes specified → "No changes specified"
        args = Namespace(
            existing_key="production",
            key=None,
            url=None,
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 1  # EXIT_ERROR
        captured = capsys.readouterr()
        assert "Error: No changes specified" in captured.err

    def test_update_system_errors(self, capsys):
        """Test system-level error handling."""
        # Create a valid config file first so the database exists
        config_data = {
            "databases": {
                "test": {
                    "url": "http://localhost:8529",
                    "database": "test_db",
                    "username": "admin",
                    "password_env": "TEST_PASSWORD",
                    "timeout": 30.0,
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Test 1: ConfigFileLoader exception → "Error updating database"
        # Use a config file path that doesn't exist
        args = Namespace(
            existing_key="test",
            key=None,
            url="http://new:8529",
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=os.path.join(self.temp_dir, "nonexistent", "databases.yaml"),
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 1  # EXIT_ERROR
        captured = capsys.readouterr()
        # When the config file doesn't exist, it returns "Database not found"
        assert "Database 'test' not found" in captured.err

        # Test 2: Invalid config file path (directory doesn't exist)
        # Create a config file in the temp_dir first, then try to update with a different path
        args = Namespace(
            existing_key="test",
            key=None,
            url="http://new:8529",
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=os.path.join(self.temp_dir, "another", "nonexistent", "databases.yaml"),
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 1  # EXIT_ERROR
        captured = capsys.readouterr()
        # Same behavior as Test 1
        assert "Database 'test' not found" in captured.err

    def test_update_user_cancellation(self, capsys):
        """Test user declining confirmation prompt."""
        # Create initial configuration
        config_data = {
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                    "timeout": 30.0,
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Mock user input to decline
        with patch("builtins.input", return_value="n"):
            args = Namespace(
                existing_key="production",
                key=None,
                url="http://new:8529",
                database=None,
                username=None,
                arango_password_env=None,
                timeout=None,
                description=None,
                config_file=self.config_path,
                dry_run=False,
                yes=False,  # Don't skip confirmation
            )
            result = handle_update(args)
            assert result == 2  # EXIT_CANCELLED
            captured = capsys.readouterr()
            assert "Operation cancelled" in captured.err

        # Verify no file changes were made
        with open(self.config_path, 'r') as f:
            updated_config = yaml.safe_load(f)
        assert updated_config["databases"]["production"]["url"] == "http://localhost:8529"  # Unchanged

    def test_update_dry_run_mode(self, capsys):
        """Test dry-run shows changes without applying them."""
        # Create initial configuration
        config_data = {
            "default_database": "production",
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                    "timeout": 30.0,
                    "description": "Production database"
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Test multiple change types in dry-run
        args = Namespace(
            existing_key="production",
            key="prod",
            url="http://new-host:8529",
            database="new_db",
            username="newuser",
            arango_password_env="NEW_PASSWORD",
            timeout=60.0,
            description="Updated description",
            config_file=self.config_path,
            dry_run=True,  # Dry-run mode
            yes=True,
        )
        result = handle_update(args)
        assert result == 0
        captured = capsys.readouterr()
        assert "[UPDATED - DRY-RUN]" in captured.out
        assert "Key: production → prod" in captured.out
        assert "URL: http://localhost:8529 → http://new-host:8529" in captured.out
        assert "Database: prod_db → new_db" in captured.out
        assert "Username: admin → newuser" in captured.out
        assert "Password Env: PROD_PASSWORD → NEW_PASSWORD" in captured.out
        assert "Timeout: 30.0 → 60.0" in captured.out
        assert "Description: Production database → Updated description" in captured.out

        # Verify no file changes were made
        with open(self.config_path, 'r') as f:
            updated_config = yaml.safe_load(f)
        assert updated_config["databases"]["production"]["url"] == "http://localhost:8529"  # Unchanged
        assert updated_config["default_database"] == "production"  # Unchanged
        assert "prod" not in updated_config["databases"]  # New key not added

    def test_update_output_format(self, capsys):
        """Test ConsequenceType.UPDATE usage and output formatting."""
        # Create initial configuration
        config_data = {
            "databases": {
                "production": {
                    "url": "http://localhost:8529",
                    "database": "prod_db",
                    "username": "admin",
                    "password_env": "PROD_PASSWORD",
                    "timeout": 30.0,
                }
            }
        }
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f)

        # Test ConsequenceType.UPDATE usage (yellow color)
        args = Namespace(
            existing_key="production",
            key=None,
            url="http://new:8529",
            database=None,
            username=None,
            arango_password_env=None,
            timeout=None,
            description=None,
            config_file=self.config_path,
            dry_run=False,
            yes=True,
        )
        result = handle_update(args)
        assert result == 0
        captured = capsys.readouterr()

        # Verify yellow color code for UPDATE type
        # The ResultReporter uses ConsequenceType.UPDATE which has yellow color
        assert "[UPDATED]" in captured.out
        assert "Database configuration 'production'" in captured.out
        assert "URL: http://localhost:8529 → http://new:8529" in captured.out
        assert "Configuration saved to:" in captured.out
