"""CLI commands for ArangoDB database management.

This module provides CLI commands for managing ArangoDB databases directly
(not YAML config files). Requires root credentials for admin operations.

Functions:
- handle_db_add() - Create ArangoDB database
- handle_db_remove() - Delete ArangoDB database
- handle_db_list() - List ArangoDB databases
"""

from __future__ import annotations

import sys
import json
from argparse import Namespace

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


def handle_db_add(args: Namespace) -> int:
    """Create a new ArangoDB database.

    Args:
        args: Parsed command-line arguments with:
            - name: Database name
            - with_user: Optional username to grant access (creates user if not exists)
            - arango_password_env: Password env var for new user
            - permission: Permission level (rw, ro, none)
            - env_file: Optional .env file path
            - dry_run: Whether to simulate only
            - yes: Skip confirmation prompt

    Returns:
        Exit code (0=success, 1=error, 2=cancelled)
    """
    # Handle --with-user atomic operation
    with_user = getattr(args, 'with_user', None)
    permission = getattr(args, 'permission', 'rw')
    
    # For dry-run mode, we show optimistic consequences (user will be created)
    # Actual behavior depends on runtime check of user existence
    reporter = ResultReporter("db add", dry_run=args.dry_run)
    reporter.add(ConsequenceType.ADD, f"Database '{args.name}'")
    if with_user:
        reporter.add(ConsequenceType.ADD, f"User '{with_user}' (active: true)")
        reporter.add(ConsequenceType.GRANT, f"Permission {permission}: {with_user} → {args.name}")

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

    # Check if database already exists
    try:
        if sys_db.has_database(args.name):
            print(f"Error: Database '{args.name}' already exists", file=sys.stderr)
            return EXIT_ERROR
    except ArangoError as e:
        print(f"Error: Failed to check database existence: {e}", file=sys.stderr)
        return EXIT_ERROR

    # Validate --with-user requirements
    user_exists = False
    user_password = None
    if with_user:
        # Check if user already exists
        try:
            user_exists = sys_db.has_user(with_user)
        except ArangoError as e:
            print(f"Error: Failed to check user existence: {e}", file=sys.stderr)
            return EXIT_ERROR

        # Only require password if user doesn't exist (we need to create them)
        if not user_exists:
            user_password = credentials.get("user_password")
            if not user_password:
                password_env = getattr(args, 'arango_password_env', 'ARANGO_PASSWORD')
                print(f"Error: {password_env} environment variable required for user creation", file=sys.stderr)
                return EXIT_ERROR
        
        # Rebuild reporter with accurate consequences based on user existence
        reporter = ResultReporter("db add", dry_run=False)
        reporter.add(ConsequenceType.ADD, f"Database '{args.name}'")
        if user_exists:
            reporter.add(ConsequenceType.EXISTS, f"User '{with_user}' (already exists)")
        else:
            reporter.add(ConsequenceType.ADD, f"User '{with_user}' (active: true)")
        reporter.add(ConsequenceType.GRANT, f"Permission {permission}: {with_user} → {args.name}")

    # Confirmation prompt
    if not confirm_action(reporter.report_prompt() + "\n\nAre you sure you want to proceed?", args):
        print("Operation cancelled", file=sys.stderr)
        return EXIT_CANCELLED

    # Execute operations
    try:
        # Create database
        sys_db.create_database(args.name)

        # Create user (if needed) and grant permission if requested
        if with_user:
            if not user_exists:
                sys_db.create_user(with_user, user_password, active=True)
            sys_db.update_permission(with_user, permission, args.name)

        # Report success
        reporter.report_result()
        return EXIT_SUCCESS

    except ArangoError as e:
        print(f"Error: Failed to create database: {e}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def handle_db_remove(args: Namespace) -> int:
    """Delete an ArangoDB database.

    Args:
        args: Parsed command-line arguments with:
            - name: Database name
            - env_file: Optional .env file path
            - dry_run: Whether to simulate only
            - yes: Skip confirmation prompt

    Returns:
        Exit code (0=success, 1=error, 2=cancelled)
    """
    # Prevent deletion of _system database (can check without connection)
    if args.name == "_system":
        print("Error: Cannot delete _system database", file=sys.stderr)
        return EXIT_ERROR

    # Build consequence list based on arguments
    reporter = ResultReporter("db remove", dry_run=args.dry_run)
    reporter.add(ConsequenceType.REMOVE, f"Database '{args.name}'")

    # Dry-run mode: report and exit without database connection
    # Note: Cannot show affected users without connection, but that's acceptable for dry-run
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

    # Check if database exists
    try:
        if not sys_db.has_database(args.name):
            print(f"Error: Database '{args.name}' not found", file=sys.stderr)
            return EXIT_ERROR
    except ArangoError as e:
        print(f"Error: Failed to check database existence: {e}", file=sys.stderr)
        return EXIT_ERROR

    # Check for users with permissions to this database (for informative output)
    try:
        all_users = sys_db.users()
        affected_users = []
        for user in all_users:
            username = user.get('username') or user.get('user')
            if username:
                try:
                    perms = sys_db.permissions(username)
                    if args.name in perms and perms[args.name] != 'none':
                        affected_users.append((username, perms[args.name]))
                except:
                    pass  # Skip users we can't query

        # Add revocation consequences
        for username, perm in affected_users:
            reporter.add(ConsequenceType.REVOKE, f"Permission: {username} → {args.name} (was: {perm})")
    except ArangoError:
        # If we can't query users, just proceed with database deletion
        pass

    # Confirmation prompt
    if not confirm_action(reporter.report_prompt() + "\n\nAre you sure you want to proceed?", args):
        print("Operation cancelled", file=sys.stderr)
        return EXIT_CANCELLED

    # Execute deletion
    try:
        sys_db.delete_database(args.name)
        reporter.report_result()
        return EXIT_SUCCESS
    except ArangoError as e:
        print(f"Error: Failed to delete database: {e}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR


def handle_db_list(args: Namespace) -> int:
    """List all ArangoDB databases.

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

    # List databases
    try:
        databases = sys_db.databases()

        # JSON output
        if getattr(args, 'json', False):
            print(json.dumps(databases, indent=2))
            return EXIT_SUCCESS

        # Human-readable output
        print(f"Databases ({len(databases)}):")
        for db_name in sorted(databases):
            marker = " (system)" if db_name == "_system" else ""
            print(f"  - {db_name}{marker}")

        return EXIT_SUCCESS
    except ArangoError as e:
        print(f"Error: Failed to list databases: {e}", file=sys.stderr)
        return EXIT_ERROR
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        return EXIT_ERROR

