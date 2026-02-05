"""CLI commands for ArangoDB user management.

This module provides CLI commands for managing ArangoDB users and permissions.
Includes both admin operations (require root) and self-service operations.

Functions:
- handle_user_add() - Create ArangoDB user (admin)
- handle_user_remove() - Delete ArangoDB user (admin)
- handle_user_list() - List ArangoDB users (admin)
- handle_user_grant() - Grant database permissions (admin)
- handle_user_revoke() - Revoke database permissions (admin)
- handle_user_databases() - List accessible databases (self-service)
- handle_user_password() - Change own password (self-service)
"""

from __future__ import annotations

import sys
import json
import logging
import os
import warnings
from argparse import Namespace

from arango import ArangoClient
from arango.exceptions import ArangoError

from .utils import (
    load_credentials,
    get_system_db,
    confirm_action,
    ResultReporter,
    ConsequenceType,
    EXIT_SUCCESS,
    EXIT_ERROR,
    EXIT_CANCELLED,
)
from ..utility.config_loader import ConfigFileLoader


def handle_user_add(args: Namespace) -> int:
    """Create a new ArangoDB user.

    Args:
        args: Parsed command-line arguments with:
            - username: Username to create
            - arango_password_env: Password env var for new user
            - active: Whether user is active (default: True)
            - env_file: Optional .env file path
            - dry_run: Whether to simulate only
            - yes: Skip confirmation prompt

    Returns:
        Exit code (0=success, 1=error, 2=cancelled)
    """
    # Get active flag
    active = getattr(args, 'active', True)

    # Build consequence list based on arguments
    reporter = ResultReporter("user add", dry_run=args.dry_run)
    reporter.add(ConsequenceType.ADD, f"User '{args.username}' (active: {str(active).lower()})")

    # Dry-run mode: report and exit without database connection
    if args.dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    # Load credentials (only needed for actual execution)
    credentials = load_credentials(args)
    if not credentials.get("root_password"):
        print("Error: ARANGO_ROOT_PASSWORD environment variable required", file=sys.stderr)
        return EXIT_ERROR

    # Connect to _system database
    sys_db = get_system_db(credentials)
    if not sys_db:
        return EXIT_ERROR

    # Check if user already exists
    try:
        if sys_db.has_user(args.username):
            print(f"Error: User '{args.username}' already exists", file=sys.stderr)
            return EXIT_ERROR
    except ArangoError as e:
        print(f"Error: Failed to check user existence: {e}", file=sys.stderr)
        return EXIT_ERROR

    # Get user password
    user_password = credentials.get("user_password")
    if not user_password:
        password_env = getattr(args, 'arango_password_env', 'ARANGO_PASSWORD')
        print(f"Error: {password_env} environment variable required for user creation", file=sys.stderr)
        return EXIT_ERROR

    # Confirmation prompt
    if not confirm_action(reporter.report_prompt() + "\n\nAre you sure you want to proceed?", args):
        print("Operation cancelled", file=sys.stderr)
        return EXIT_CANCELLED

    # Execute operation
    try:
        sys_db.create_user(args.username, user_password, active=active)
        reporter.report_result()
        return EXIT_SUCCESS
    except ArangoError as e:
        print(f"Error: Failed to create user: {e}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def handle_user_remove(args: Namespace) -> int:
    """Delete an ArangoDB user.

    Args:
        args: Parsed command-line arguments with:
            - username: Username to delete
            - env_file: Optional .env file path
            - dry_run: Whether to simulate only
            - yes: Skip confirmation prompt

    Returns:
        Exit code (0=success, 1=error, 2=cancelled)
    """
    # Prevent deletion of root user (can check without connection)
    if args.username == "root":
        print("Error: Cannot delete root user", file=sys.stderr)
        return EXIT_ERROR

    # Build consequence list based on arguments
    reporter = ResultReporter("user remove", dry_run=args.dry_run)
    reporter.add(ConsequenceType.REMOVE, f"User '{args.username}'")

    # Dry-run mode: report and exit without database connection
    # Note: Cannot show revoked permissions without connection, but that's acceptable for dry-run
    if args.dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    # Load credentials (only needed for actual execution)
    credentials = load_credentials(args)
    if not credentials.get("root_password"):
        print("Error: ARANGO_ROOT_PASSWORD environment variable required", file=sys.stderr)
        return EXIT_ERROR

    # Connect to _system database
    sys_db = get_system_db(credentials)
    if not sys_db:
        return EXIT_ERROR

    # Check if user exists
    try:
        if not sys_db.has_user(args.username):
            print(f"Error: User '{args.username}' not found", file=sys.stderr)
            return EXIT_ERROR
    except ArangoError as e:
        print(f"Error: Failed to check user existence: {e}", file=sys.stderr)
        return EXIT_ERROR

    # Check for user's database permissions (for informative output)
    try:
        perms = sys_db.permissions(args.username)
        for db_name, perm in perms.items():
            if perm != 'none':
                reporter.add(ConsequenceType.REVOKE, f"Permission: {args.username} → {db_name} (was: {perm})")
    except ArangoError:
        # If we can't query permissions, just proceed with user deletion
        pass

    # Confirmation prompt
    if not confirm_action(reporter.report_prompt() + "\n\nAre you sure you want to proceed?", args):
        print("Operation cancelled", file=sys.stderr)
        return EXIT_CANCELLED

    # Execute deletion
    try:
        sys_db.delete_user(args.username)
        reporter.report_result()
        return EXIT_SUCCESS
    except ArangoError as e:
        print(f"Error: Failed to delete user: {e}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def handle_user_list(args: Namespace) -> int:
    """List all ArangoDB users.

    Args:
        args: Parsed command-line arguments with:
            - env_file: Optional .env file path
            - json: Output as JSON

    Returns:
        Exit code (0=success, 1=error)
    """
    # Load credentials
    credentials = load_credentials(args)
    if not credentials.get("root_password"):
        print("Error: ARANGO_ROOT_PASSWORD environment variable required", file=sys.stderr)
        return EXIT_ERROR

    # Connect to _system database
    sys_db = get_system_db(credentials)
    if not sys_db:
        return EXIT_ERROR

    # List users
    try:
        users = sys_db.users()

        # JSON output
        if getattr(args, 'json', False):
            print(json.dumps(users, indent=2))
            return EXIT_SUCCESS

        # Human-readable output
        print(f"Users ({len(users)}):")
        for user in sorted(users, key=lambda u: u.get('username', u.get('user', ''))):
            username = user.get('username') or user.get('user')
            active = user.get('active', True)
            status = "active" if active else "inactive"
            print(f"  - {username} ({status})")

        return EXIT_SUCCESS
    except ArangoError as e:
        print(f"Error: Failed to list users: {e}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def handle_user_grant(args: Namespace) -> int:
    """Grant database permissions to a user.

    Args:
        args: Parsed command-line arguments with:
            - username: Username to grant permissions to
            - database: Database name
            - permission: Permission level (rw, ro, none)
            - env_file: Optional .env file path
            - dry_run: Whether to simulate only
            - yes: Skip confirmation prompt

    Returns:
        Exit code (0=success, 1=error, 2=cancelled)
    """
    # Get permission level
    permission = getattr(args, 'permission', 'rw')

    # Build consequence list based on arguments
    reporter = ResultReporter("user grant", dry_run=args.dry_run)
    reporter.add(ConsequenceType.GRANT, f"Permission {permission}: {args.username} → {args.database}")

    # Dry-run mode: report and exit without database connection
    if args.dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    # Load credentials (only needed for actual execution)
    credentials = load_credentials(args)
    if not credentials.get("root_password"):
        print("Error: ARANGO_ROOT_PASSWORD environment variable required", file=sys.stderr)
        return EXIT_ERROR

    # Connect to _system database
    sys_db = get_system_db(credentials)
    if not sys_db:
        return EXIT_ERROR

    # Check if user exists
    try:
        if not sys_db.has_user(args.username):
            print(f"Error: User '{args.username}' not found", file=sys.stderr)
            return EXIT_ERROR
    except ArangoError as e:
        print(f"Error: Failed to check user existence: {e}", file=sys.stderr)
        return EXIT_ERROR

    # Check if database exists
    try:
        if not sys_db.has_database(args.database):
            print(f"Error: Database '{args.database}' not found", file=sys.stderr)
            return EXIT_ERROR
    except ArangoError as e:
        print(f"Error: Failed to check database existence: {e}", file=sys.stderr)
        return EXIT_ERROR

    # Confirmation prompt
    if not confirm_action(reporter.report_prompt() + "\n\nAre you sure you want to proceed?", args):
        print("Operation cancelled", file=sys.stderr)
        return EXIT_CANCELLED

    # Execute operation
    try:
        sys_db.update_permission(args.username, permission, args.database)
        reporter.report_result()
        return EXIT_SUCCESS
    except ArangoError as e:
        print(f"Error: Failed to grant permission: {e}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def handle_user_revoke(args: Namespace) -> int:
    """Revoke database permissions from a user.

    Args:
        args: Parsed command-line arguments with:
            - username: Username to revoke permissions from
            - database: Database name
            - env_file: Optional .env file path
            - dry_run: Whether to simulate only
            - yes: Skip confirmation prompt

    Returns:
        Exit code (0=success, 1=error, 2=cancelled)
    """
    # Build consequence list based on arguments
    # Note: Cannot show current permission without connection - acceptable for dry-run
    reporter = ResultReporter("user revoke", dry_run=args.dry_run)
    reporter.add(ConsequenceType.REVOKE, f"Permission: {args.username} → {args.database}")

    # Dry-run mode: report and exit without database connection
    if args.dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    # Load credentials (only needed for actual execution)
    credentials = load_credentials(args)
    if not credentials.get("root_password"):
        print("Error: ARANGO_ROOT_PASSWORD environment variable required", file=sys.stderr)
        return EXIT_ERROR

    # Connect to _system database
    sys_db = get_system_db(credentials)
    if not sys_db:
        return EXIT_ERROR

    # Check if user exists
    try:
        if not sys_db.has_user(args.username):
            print(f"Error: User '{args.username}' not found", file=sys.stderr)
            return EXIT_ERROR
    except ArangoError as e:
        print(f"Error: Failed to check user existence: {e}", file=sys.stderr)
        return EXIT_ERROR

    # Get current permission (for informative output)
    current_perm = None
    try:
        perms = sys_db.permissions(args.username)
        current_perm = perms.get(args.database, 'none')
        # Update consequence with current permission info
        if current_perm and current_perm != 'none':
            reporter.consequences.clear()
            reporter.add(ConsequenceType.REVOKE, f"Permission: {args.username} → {args.database} (was: {current_perm})")
    except ArangoError:
        pass

    # Confirmation prompt
    if not confirm_action(reporter.report_prompt() + "\n\nAre you sure you want to proceed?", args):
        print("Operation cancelled", file=sys.stderr)
        return EXIT_CANCELLED

    # Execute operation
    try:
        sys_db.reset_permission(args.username, args.database)
        reporter.report_result()
        return EXIT_SUCCESS
    except ArangoError as e:
        print(f"Error: Failed to revoke permission: {e}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def _connect_as_user(credentials: dict, username: str, password: str) -> tuple:
    """Connect to ArangoDB as a specific user.

    Uses the database resolution system via ConfigFileLoader:
    1. Load configured databases from YAML config or environment variables
    2. Try each configured database in order until one works
    3. Fall back to _system only if no configured databases exist
    
    This leverages the existing multi-tenancy configuration system, ensuring
    non-root users can connect using databases they have access to.
    
    Args:
        credentials: Dictionary with:
            - 'url': ArangoDB server URL (fallback if no config)
            - '_env_vars': Dict of env var names for error messages
        username: Username to authenticate as
        password: Password for authentication
        
    Returns:
        Tuple of (db_connection, error_message). If successful, error_message is None.
        If failed, db_connection is None and error_message contains the error.
    """
    env_vars = credentials.get("_env_vars", {})
    
    # Load database configurations using ConfigFileLoader
    # This respects YAML config files AND environment variables (ARANGO_DB, etc.)
    config_loader = ConfigFileLoader()
    config_loader.load()
    configured_dbs = config_loader.get_configured_databases()
    
    # Build list of (url, database_name, source_description) tuples to try
    databases_to_try = []
    
    if configured_dbs:
        # Use configured databases - they contain URL, database name, etc.
        for db_key, db_config in configured_dbs.items():
            source = "YAML config" if config_loader.loaded_from_yaml else "environment variables"
            databases_to_try.append((
                db_config.url,
                db_config.database,
                f"{db_key} (from {source})"
            ))
    else:
        # No configuration found - use credentials URL and fall back to _system
        databases_to_try.append((
            credentials.get("url", "http://localhost:8529"),
            "_system",
            "fallback (no config)"
        ))
    
    last_error = None
    attempted = []
    
    for url, db_name, source in databases_to_try:
        attempted.append(f"'{db_name}' at {url} ({source})")
        try:
            client = ArangoClient(hosts=url)
            db = client.db(db_name, username=username, password=password)
            # Validate connection by calling a lightweight endpoint
            # This will fail fast if authentication or authorization fails
            _ = db.databases_accessible_to_user()
            return db, None
        except ArangoError as e:
            last_error = e
            # Continue to try next database
            continue
        except Exception as e:
            error_msg = str(e)
            if "Connection refused" in error_msg or "NewConnectionError" in error_msg:
                return None, (
                    f"Cannot connect to ArangoDB at {url}\n"
                    f"  Source: {source}\n"
                    "Hint: Is the ArangoDB server running?"
                )
            elif "timeout" in error_msg.lower():
                return None, (
                    f"Connection to ArangoDB timed out\n"
                    f"  URL: {url} ({source})"
                )
            else:
                last_error = e
                continue
    
    # All database attempts failed - provide detailed error message
    config_source = "YAML config" if config_loader.loaded_from_yaml else "environment variables"
    error_details = [
        f"Failed to authenticate user '{username}' to ArangoDB",
        f"  Configuration source: {config_source}",
        f"  Username source: {env_vars.get('username_env', 'ARANGO_USERNAME')}",
        f"  Password source: {env_vars.get('user_password_env', 'ARANGO_PASSWORD')}",
        "",
        "  Attempted connections:",
    ]
    for attempt in attempted:
        error_details.append(f"    - {attempt}")
    
    if last_error:
        error_details.append("")
        error_details.append(f"  Last error: {last_error}")
    
    error_details.append("")
    error_details.append("Hints:")
    error_details.append("  - Verify your credentials are correct")
    error_details.append("  - Set ARANGO_DB to a database you have access to")
    error_details.append("  - Non-root users typically cannot access '_system' database")
    if not config_loader.loaded_from_yaml:
        error_details.append("  - Or create a config file with 'mcp-arangodb-async db add'")
    
    return None, "\n".join(error_details)


def handle_user_databases(args: Namespace) -> int:
    """List databases accessible to current user (self-service).

    Args:
        args: Parsed command-line arguments with:
            - env_file: Optional .env file path
            - json: Output as JSON

    Returns:
        Exit code (0=success, 1=error)
    """
    # Load credentials
    credentials = load_credentials(args)
    username = credentials.get("username", "root")
    user_password = credentials.get("user_password")

    if not user_password:
        password_env = getattr(args, 'arango_password_env', 'ARANGO_PASSWORD')
        print(f"Error: {password_env} environment variable required", file=sys.stderr)
        return EXIT_ERROR

    # Suppress urllib3 warnings for cleaner output
    logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

    # Connect as the user
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=Warning, module="urllib3")
        db, error = _connect_as_user(credentials, username, user_password)
        if error:
            print(f"Error: {error}", file=sys.stderr)
            return EXIT_ERROR

    # Get user's accessible databases using the proper API
    try:
        # Use databases_accessible_to_user() which calls /_api/database/user
        # This endpoint returns databases the authenticated user can access
        accessible_dbs = db.databases_accessible_to_user()

        # JSON output
        if getattr(args, 'json', False):
            # Convert to dict format with "rw" permission for consistency
            # (the API only returns databases user has access to)
            result = {db_name: "accessible" for db_name in accessible_dbs}
            print(json.dumps(result, indent=2))
            return EXIT_SUCCESS

        # Human-readable output
        print(f"Accessible databases for user '{username}' ({len(accessible_dbs)}):")
        for db_name in sorted(accessible_dbs):
            print(f"  - {db_name}")

        return EXIT_SUCCESS
    except ArangoError as e:
        print(f"Error: Failed to list databases: {e}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def handle_user_password(args: Namespace) -> int:
    """Change current user's password (self-service).

    Args:
        args: Parsed command-line arguments with:
            - env_file: Optional .env file path
            - new_password_env: Env var name for new password
            - dry_run: Whether to simulate only
            - yes: Skip confirmation prompt

    Returns:
        Exit code (0=success, 1=error, 2=cancelled)
    """
    # Load credentials first (loads dotenv file, then retrieves all env vars)
    # This ensures ARANGO_USERNAME and ARANGO_NEW_PASSWORD are available
    credentials = load_credentials(args)
    username = credentials.get("username", "root")

    # Build consequence list based on arguments
    reporter = ResultReporter("user password", dry_run=args.dry_run)
    reporter.add(ConsequenceType.UPDATE, f"Password for user '{username}'")

    # Dry-run mode: report and exit without database connection
    if args.dry_run:
        reporter.report_result()
        return EXIT_SUCCESS

    # Validate credentials (already loaded above)
    current_password = credentials.get("user_password")

    if not current_password:
        password_env = credentials.get("_env_vars", {}).get("user_password_env", "ARANGO_PASSWORD")
        print(f"Error: {password_env} environment variable required", file=sys.stderr)
        return EXIT_ERROR

    # Get new password from credentials (loaded via CLIEnvVar enum)
    new_password = credentials.get("new_password")
    if not new_password:
        new_password_env = credentials.get("_env_vars", {}).get("new_password_env", "ARANGO_NEW_PASSWORD")
        print(f"Error: {new_password_env} environment variable required", file=sys.stderr)
        return EXIT_ERROR

    # Suppress urllib3 warnings for cleaner output
    logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

    # Connect as the user (users can update their own password per ArangoDB API)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=Warning, module="urllib3")
        db, error = _connect_as_user(credentials, username, current_password)
        if error:
            print(f"Error: {error}", file=sys.stderr)
            return EXIT_ERROR

    # Confirmation prompt
    if not confirm_action(reporter.report_prompt() + "\n\nAre you sure you want to proceed?", args):
        print("Operation cancelled", file=sys.stderr)
        return EXIT_CANCELLED

    # Execute operation - users can update their own password
    try:
        db.update_user(username, password=new_password)
        reporter.report_result()
        return EXIT_SUCCESS
    except ArangoError as e:
        print(f"Error: Failed to change password: {e}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR

