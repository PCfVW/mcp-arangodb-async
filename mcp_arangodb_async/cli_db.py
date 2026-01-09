"""CLI tool for database configuration management.

This module provides command-line interface for managing database configurations
in the YAML config file. Admin-only (requires file system access).

Functions:
- handle_add() - Add a new database configuration
- handle_remove() - Remove a database configuration
- handle_list() - List all configured databases
- handle_test() - Test database connection
- handle_status() - Show database resolution status
- handle_update() - Update a database configuration
"""

from __future__ import annotations

import sys
import json
import os
import asyncio
from typing import Any, Dict
from argparse import Namespace

from .config_loader import ConfigFileLoader
from .multi_db_manager import DatabaseConfig, MultiDatabaseConnectionManager


def handle_add(args: Namespace) -> int:
    """Add a new database configuration.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error, 2 for cancelled)
    """
    from .cli_utils import ResultReporter, ConsequenceType, confirm_action, EXIT_SUCCESS, EXIT_ERROR, EXIT_CANCELLED

    # Build consequence list based on arguments
    dry_run = getattr(args, 'dry_run', False)
    reporter = ResultReporter("db config add", dry_run=dry_run)
    reporter.add(ConsequenceType.ADD, f"Database configuration '{args.key}'")
    reporter.add(ConsequenceType.ADD, f"  URL: {args.url}")
    reporter.add(ConsequenceType.ADD, f"  Database: {args.database}")
    reporter.add(ConsequenceType.ADD, f"  Username: {args.username}")
    reporter.add(ConsequenceType.ADD, f"  Password Env: {args.arango_password_env}")

    # Dry-run mode: report and exit
    if dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    try:
        # Load existing configuration from YAML only (don't merge with env vars)
        # This ensures we only add what the user explicitly requests
        loader = ConfigFileLoader(args.config_file)
        loader.load_yaml_only()

        # Check for duplicate key
        existing_databases = loader.get_configured_databases()
        if args.key in existing_databases:
            print(f"Error: Database '{args.key}' already exists", file=sys.stderr)
            print("Use 'db remove' to remove it first, or choose a different key", file=sys.stderr)
            return EXIT_ERROR

        # Confirmation prompt
        if not confirm_action(reporter.report_prompt() + "\n\nAre you sure you want to proceed?", args):
            print("Operation cancelled", file=sys.stderr)
            return EXIT_CANCELLED

        # Create new database configuration
        new_config = DatabaseConfig(
            url=args.url,
            database=args.database,
            username=args.username,
            password_env=args.arango_password_env,
            timeout=args.timeout,
            description=args.description
        )

        # Add and save
        loader.add_database(args.key, new_config)
        loader.save_to_yaml()

        # Report success
        reporter.report_result()
        print(f"\nConfiguration saved to: {loader.config_path}")

        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error adding database: {e}", file=sys.stderr)
        return EXIT_ERROR


def handle_remove(args: Namespace) -> int:
    """Remove a database configuration.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error, 2 for cancelled)
    """
    from .cli_utils import ResultReporter, ConsequenceType, confirm_action, EXIT_SUCCESS, EXIT_ERROR, EXIT_CANCELLED

    # Build consequence list based on arguments
    dry_run = getattr(args, 'dry_run', False)
    reporter = ResultReporter("db config remove", dry_run=dry_run)
    reporter.add(ConsequenceType.REMOVE, f"Database configuration '{args.key}'")

    # Dry-run mode: report and exit
    if dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    try:
        # Load existing configuration from YAML only (don't merge with env vars)
        # This ensures we only operate on explicitly configured databases
        loader = ConfigFileLoader(args.config_file)
        loader.load_yaml_only()

        # Check if database exists
        existing_databases = loader.get_configured_databases()
        if args.key not in existing_databases:
            print(f"Error: Database '{args.key}' not found", file=sys.stderr)
            return EXIT_ERROR

        # Confirmation prompt
        if not confirm_action(reporter.report_prompt() + "\n\nAre you sure you want to proceed?", args):
            print("Operation cancelled", file=sys.stderr)
            return EXIT_CANCELLED

        # Remove and save
        loader.remove_database(args.key)
        loader.save_to_yaml()

        # Report success
        reporter.report_result()
        print(f"Configuration saved to: {loader.config_path}")

        return EXIT_SUCCESS
    except Exception as e:
        print(f"Error removing database: {e}", file=sys.stderr)
        return EXIT_ERROR


def handle_list(args: Namespace) -> int:
    """List all configured databases.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Load configuration
        loader = ConfigFileLoader(args.config_file)
        loader.load()
        
        databases = loader.get_configured_databases()
        
        # Check if config was loaded from YAML file or environment variables
        if not loader.loaded_from_yaml:
            # No config file - indicate graceful degradation
            print(f"No config file at expected path: {loader.config_path}")
            print()
            if databases:
                print("Database information from environment variables:")
                print()
                for key, config in databases.items():
                    print(f"  {key}:")
                    print(f"    URL: {config.url}")
                    print(f"    Database: {config.database}")
                    print(f"    Username: {config.username}")
                    print(f"    Password env: {config.password_env}")
                    print(f"    Timeout: {config.timeout}s")
                    if config.description:
                        print(f"    Description: {config.description}")
                    print()
                print("Note: Create a config file to define multiple databases and customize settings.")
            else:
                print("No database configuration found in environment variables.")
                print("Note: Create a config file or set ARANGO_URL, ARANGO_DB, ARANGO_USERNAME environment variables.")
            return 0
        
        # Config file exists
        if not databases:
            print("No databases configured")
            print(f"Configuration file: {loader.config_path}")
            return 0
        
        print(f"Configured databases ({len(databases)}):")
        print(f"Configuration file: {loader.config_path}")
        if loader.default_database:
            print(f"Default database: {loader.default_database}")
        print()
        
        for key, config in databases.items():
            print(f"  {key}:")
            print(f"    URL: {config.url}")
            print(f"    Database: {config.database}")
            print(f"    Username: {config.username}")
            print(f"    Password env: {config.password_env}")
            print(f"    Timeout: {config.timeout}s")
            if config.description:
                print(f"    Description: {config.description}")
            print()

        return 0
    except Exception as e:
        print(f"Error listing databases: {e}", file=sys.stderr)
        return 1


def handle_test(args: Namespace) -> int:
    """Test database connection.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Load credentials from --env-file if specified
        if hasattr(args, 'env_file') and args.env_file:
            from .cli_utils import load_credentials
            load_credentials(args)
        
        # Load configuration
        loader = ConfigFileLoader(args.config_file)
        loader.load()

        databases = loader.get_configured_databases()
        if args.key not in databases:
            print(f"Error: Database '{args.key}' not found", file=sys.stderr)
            return 1

        # Test connection using MultiDatabaseConnectionManager
        async def test_connection():
            db_manager = MultiDatabaseConnectionManager()
            db_manager.register_database(args.key, databases[args.key])
            result = await db_manager.test_connection(args.key)
            await db_manager.close_all()
            return result

        result = asyncio.run(test_connection())

        if result["connected"]:
            print(f"✓ Connection to '{args.key}' successful")
            print(f"  ArangoDB version: {result['version']}")
            return 0
        else:
            print(f"✗ Connection to '{args.key}' failed", file=sys.stderr)
            print(f"  Error: {result['error']}", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"Error testing connection: {e}", file=sys.stderr)
        return 1


def handle_status(args: Namespace) -> int:
    """Show database resolution status.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        # Load configuration
        loader = ConfigFileLoader(args.config_file)
        loader.load()

        databases = loader.get_configured_databases()

        print("Database Resolution Status:")
        print(f"Configuration file: {loader.config_path}")
        print()

        # Show default database
        if loader.default_database:
            print(f"Default database (from config): {loader.default_database}")
        else:
            print("Default database (from config): Not set")

        # Show environment variable
        env_default = os.getenv("ARANGO_DB")
        if env_default:
            print(f"Default database (from ARANGO_DB): {env_default}")
        else:
            print("Default database (from ARANGO_DB): Not set")

        print()
        print(f"Configured databases: {len(databases)}")
        for key in databases.keys():
            print(f"  - {key}")

        print()
        print("Resolution order:")
        print("  1. Tool argument (database parameter)")
        print("  2. Focused database (session state)")
        print("  3. Config default (from YAML)")
        print("  4. Environment variable (ARANGO_DB)")
        print("  5. First configured database")
        print("  6. Fallback to '_system'")

        return 0
    except Exception as e:
        print(f"Error showing status: {e}", file=sys.stderr)
        return 1


def handle_update(args: Namespace) -> int:
    """Update a database configuration.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, 1 for error, 2 for cancelled)
    """
    from .cli_utils import ResultReporter, ConsequenceType, confirm_action, EXIT_SUCCESS, EXIT_ERROR, EXIT_CANCELLED

    # Initialize reporter
    dry_run = getattr(args, 'dry_run', False)
    reporter = ResultReporter("db config update", dry_run=dry_run)

    try:
        # Load existing configuration from YAML only
        loader = ConfigFileLoader(args.config_file)
        loader.load_yaml_only()
        
        existing_databases = loader.get_configured_databases()
        
        # Validate existing key exists
        if args.existing_key not in existing_databases:
            print(f"Error: Database '{args.existing_key}' not found", file=sys.stderr)
            return EXIT_ERROR
        
        existing_config = existing_databases[args.existing_key]
        
        # Determine final key (use new key if provided, otherwise keep existing)
        final_key = args.key if args.key else args.existing_key
        
        # Validate new key doesn't conflict (if changing key)
        if args.key and args.key in existing_databases and args.key != args.existing_key:
            print(f"Error: Database '{args.key}' already exists", file=sys.stderr)
            return EXIT_ERROR
        
        # Build updated configuration by merging existing with new values
        # Description: None = no change, "" = clear it, "text" = set new value
        if args.description is None:
            new_description = existing_config.description  # Keep existing
        elif args.description == "":
            new_description = None  # Clear it
        else:
            new_description = args.description  # Set new value
        
        updated_config = DatabaseConfig(
            url=args.url if args.url else existing_config.url,
            database=args.database if args.database else existing_config.database,
            username=args.username if args.username else existing_config.username,
            password_env=args.arango_password_env if args.arango_password_env else existing_config.password_env,
            timeout=args.timeout if args.timeout is not None else existing_config.timeout,
            description=new_description,
        )
        
        # Check if any changes are specified
        has_changes = (
            args.key or
            args.url or
            args.database or
            args.username or
            args.arango_password_env or
            args.timeout is not None or
            args.description is not None  # includes "" (clear)
        )
        
        if not has_changes:
            print("Error: No changes specified", file=sys.stderr)
            return EXIT_ERROR
        
        # Build consequence list
        if args.key and args.key != args.existing_key:
            reporter.add(ConsequenceType.UPDATE, f"Database configuration '{args.existing_key}'")
            reporter.add(ConsequenceType.UPDATE, f"  Key: {args.existing_key} → {args.key}")
        else:
            reporter.add(ConsequenceType.UPDATE, f"Database configuration '{args.existing_key}'")
        
        # Add field changes
        if args.url:
            reporter.add(ConsequenceType.UPDATE, f"  URL: {existing_config.url} → {args.url}")
        if args.database:
            reporter.add(ConsequenceType.UPDATE, f"  Database: {existing_config.database} → {args.database}")
        if args.username:
            reporter.add(ConsequenceType.UPDATE, f"  Username: {existing_config.username} → {args.username}")
        if args.arango_password_env:
            reporter.add(ConsequenceType.UPDATE, f"  Password Env: {existing_config.password_env} → {args.arango_password_env}")
        if args.timeout is not None:
            reporter.add(ConsequenceType.UPDATE, f"  Timeout: {existing_config.timeout} → {args.timeout}")
        if args.description is not None:
            old_desc = existing_config.description or "(not set)"
            new_desc = args.description or "(not set)"
            reporter.add(ConsequenceType.UPDATE, f"  Description: {old_desc} → {new_desc}")
        
        # Dry-run mode: report and exit
        if dry_run:
            reporter.report_result()
            return EXIT_SUCCESS
        
        # Confirmation prompt
        if not confirm_action(reporter.report_prompt() + "\n\nAre you sure you want to proceed?", args):
            print("Operation cancelled", file=sys.stderr)
            return EXIT_CANCELLED
        
        # Update default_database reference if key is being renamed and it's the default
        if args.key and loader.default_database == args.existing_key:
            loader.default_database = args.key
        
        # Use remove+add pattern to update
        loader.remove_database(args.existing_key)
        loader.add_database(final_key, updated_config)
        
        # Save changes
        loader.save_to_yaml()
        
        # Report success
        reporter.report_result()
        print(f"\nConfiguration saved to: {loader.config_path}")
        
        return EXIT_SUCCESS
        
    except Exception as e:
        print(f"Error updating database: {e}", file=sys.stderr)
        return EXIT_ERROR
