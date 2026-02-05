"""CLI utilities for admin commands.

This module provides shared utilities for CLI commands including:
- Credential loading from environment files
- Result reporting with color-coded output
- Confirmation prompts with dry-run support
- Database connection utilities
- Exit code constants

Functions:
- load_credentials() - Load credentials from env file or environment
- confirm_action() - Interactive confirmation with --yes bypass
- get_system_db() - Connect to _system database with warning suppression
- ResultReporter - Color-coded result reporting class

Enums:
- CLIEnvVar - All supported CLI environment variables (auto-loaded from dotenv)
"""

from __future__ import annotations

import logging
import os
import sys
import warnings
from typing import Optional, Dict, Any
from argparse import Namespace
from enum import Enum

from arango import ArangoClient
from arango.database import StandardDatabase
from arango.exceptions import ArangoError

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CANCELLED = 2


class CLIEnvVar(Enum):
    """All supported CLI environment variables.
    
    These environment variables are automatically loaded from the dotenv file
    specified via --env-file. Developers adding new environment variables
    should add them to this enum to ensure they are:
    1. Automatically loaded from dotenv files
    2. Documented in a centralized location
    3. Consistently named and accessible
    
    Each enum value is a tuple of:
    - var_name: The actual environment variable name (e.g., "ARANGO_PASSWORD")
    - description: Human-readable description for documentation
    - default: Default value if not set (None means required)
    - category: Logical grouping (connection, auth, config)
    
    Usage:
        credentials = load_credentials(args)
        password = credentials.get(CLIEnvVar.ARANGO_PASSWORD.key)
        
    Or use the helper method:
        password = CLIEnvVar.ARANGO_PASSWORD.get()  # After dotenv is loaded
    """
    
    # Connection settings
    ARANGO_URL = ("ARANGO_URL", "ArangoDB server URL", "http://localhost:8529", "connection")
    ARANGO_DB = ("ARANGO_DB", "Default database name", None, "connection")
    
    # Authentication - Admin
    ARANGO_ROOT_PASSWORD = ("ARANGO_ROOT_PASSWORD", "Root password for admin operations", None, "auth")
    
    # Authentication - User
    ARANGO_USERNAME = ("ARANGO_USERNAME", "Username for user operations", "root", "auth")
    ARANGO_PASSWORD = ("ARANGO_PASSWORD", "Password for user operations", None, "auth")
    ARANGO_NEW_PASSWORD = ("ARANGO_NEW_PASSWORD", "New password for password change", None, "auth")
    
    # Configuration
    LOG_LEVEL = ("LOG_LEVEL", "Logging level (DEBUG, INFO, WARNING, ERROR)", None, "config")
    
    def __init__(self, var_name: str, description: str, default: Optional[str], category: str):
        self.var_name = var_name
        self.description = description
        self.default_value = default
        self.category = category
    
    @property
    def key(self) -> str:
        """Return the key to use in credentials dict (lowercase without ARANGO_ prefix)."""
        name = self.var_name
        if name.startswith("ARANGO_"):
            name = name[7:]  # Remove "ARANGO_" prefix
        return name.lower()
    
    def get(self, default: Optional[str] = None) -> Optional[str]:
        """Get the value from environment, falling back to default.
        
        Args:
            default: Override default value (uses enum default if not provided)
            
        Returns:
            Environment variable value or default
        """
        if default is None:
            default = self.default_value
        return os.getenv(self.var_name, default)
    
    @classmethod
    def get_by_category(cls, category: str) -> list["CLIEnvVar"]:
        """Get all env vars in a category.
        
        Args:
            category: Category name (connection, auth, config)
            
        Returns:
            List of CLIEnvVar members in that category
        """
        return [e for e in cls if e.category == category]
    
    @classmethod
    def get_all_names(cls) -> list[str]:
        """Get all environment variable names.
        
        Returns:
            List of all env var names (e.g., ["ARANGO_URL", "ARANGO_DB", ...])
        """
        return [e.var_name for e in cls]


# ANSI color codes
class Color(Enum):
    """ANSI color codes for terminal output.
    
    Uses SGR (Select Graphic Rendition) parameters:
    - Bright/bold: codes 90-97 (bright colors) or 1;3x (bold + color)
    - Dim: code 2 combined with color (2;3x)
    - Standard: codes 30-37
    """
    # Bright colors for execution results (completed actions)
    GREEN = "\033[92m"       # Bright green
    RED = "\033[91m"         # Bright red
    YELLOW = "\033[93m"      # Bright yellow
    # Dim colors for confirmation prompts (pending actions)
    GREEN_DIM = "\033[2;32m" # Dim green (SGR 2 = dim, 32 = green)
    RED_DIM = "\033[2;31m"   # Dim red (SGR 2 = dim, 31 = red)
    YELLOW_DIM = "\033[2;33m" # Dim yellow (SGR 2 = dim, 33 = yellow)
    # Utility colors
    GRAY = "\033[90m"        # Bright black (gray)
    RESET = "\033[0m"        # Reset all attributes


class ConsequenceType(Enum):
    """Consequence types for result reporting.
    
    Each type defines both present and past tense labels:
    - Present tense (prompt_label): Used in confirmation prompts for pending actions
    - Past tense (result_label): Used in execution results for completed actions
    
    Colors:
    - prompt_color: Dimmed color for confirmation prompts (not yet executed)
    - result_color: Bright color for execution results (completed)
    """
    # Additive/constructive actions (green)
    ADD = ("ADD", "ADDED", Color.GREEN_DIM, Color.GREEN)
    CREATE = ("CREATE", "CREATED", Color.GREEN_DIM, Color.GREEN)
    GRANT = ("GRANT", "GRANTED", Color.GREEN_DIM, Color.GREEN)
    # Destructive actions (red)
    REMOVE = ("REMOVE", "REMOVED", Color.RED_DIM, Color.RED)
    REVOKE = ("REVOKE", "REVOKED", Color.RED_DIM, Color.RED)
    # Modification actions (yellow)
    UPDATE = ("UPDATE", "UPDATED", Color.YELLOW_DIM, Color.YELLOW)
    # Informational types (gray) - no tense change
    EXISTS = ("EXISTS", "EXISTS", Color.GRAY, Color.GRAY)
    
    def __init__(self, prompt_label: str, result_label: str, prompt_color: Color, result_color: Color):
        self.prompt_label = prompt_label  # Present tense: "ADD", "REMOVE"
        self.result_label = result_label  # Past tense: "ADDED", "REMOVED"
        self.prompt_color = prompt_color
        self.result_color = result_color


def load_credentials(args: Namespace) -> Dict[str, Any]:
    """Load credentials from environment file or environment variables.
    
    Loads all environment variables defined in CLIEnvVar after loading
    the dotenv file (if specified). This ensures consistent access to
    all supported environment variables.

    Args:
        args: Parsed command-line arguments with optional env_file,
              arango_root_password_env, arango_password_env, url attributes

    Returns:
        Dictionary with credentials:
        - root_password: Root password for admin operations
        - user_password: User password for self-service operations  
        - new_password: New password for password change operations
        - url: ArangoDB server URL (--url arg takes precedence over env)
        - username: Username for self-service operations
        - database: Database name from environment
        - _env_vars: Dictionary mapping credential keys to their env var names
    """
    # Load from dotenv file if specified (MUST happen before any os.getenv calls)
    # Use override=True to ensure CLI-specified env file takes precedence over
    # any previously loaded .env files (e.g., from config.py module import)
    if hasattr(args, 'env_file') and args.env_file:
        try:
            from dotenv import load_dotenv
            load_dotenv(args.env_file, override=True)
        except ImportError:
            print("Warning: python-dotenv not installed, skipping .env file", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Failed to load .env file: {e}", file=sys.stderr)

    # Determine variable names (use CLI overrides or defaults from enum)
    root_pw_var = getattr(args, 'arango_root_password_env', None) or CLIEnvVar.ARANGO_ROOT_PASSWORD.var_name
    user_pw_var = getattr(args, 'arango_password_env', None) or CLIEnvVar.ARANGO_PASSWORD.var_name
    new_pw_var = getattr(args, 'new_password_env', None) or CLIEnvVar.ARANGO_NEW_PASSWORD.var_name

    # URL: command-line argument takes precedence over environment variable
    url = getattr(args, 'url', None) or CLIEnvVar.ARANGO_URL.get()

    # Retrieve values from environment using CLIEnvVar
    return {
        "root_password": os.getenv(root_pw_var),
        "user_password": os.getenv(user_pw_var),
        "new_password": os.getenv(new_pw_var),  # New: for password change
        "url": url,
        "username": CLIEnvVar.ARANGO_USERNAME.get(),
        "database": CLIEnvVar.ARANGO_DB.get(),  # May be None if not set
        # Include env var names for error messages (never expose actual values)
        "_env_vars": {
            "root_password_env": root_pw_var,
            "user_password_env": user_pw_var,
            "new_password_env": new_pw_var,
            "url_env": CLIEnvVar.ARANGO_URL.var_name,
            "username_env": CLIEnvVar.ARANGO_USERNAME.var_name,
            "database_env": CLIEnvVar.ARANGO_DB.var_name,
        },
    }


def get_system_db(credentials: dict) -> Optional[StandardDatabase]:
    """Connect to _system database as root for admin operations.

    Suppresses urllib3 connection warnings for cleaner error output.

    Args:
        credentials: Dictionary with 'url' and 'root_password' keys

    Returns:
        StandardDatabase instance for _system database, or None on error
    """
    # Suppress urllib3 retry warnings for cleaner output
    logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

    # Also suppress urllib3 InsecureRequestWarning and other warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=Warning, module="urllib3")

        try:
            client = ArangoClient(hosts=credentials["url"])
            sys_db = client.db("_system", username="root", password=credentials["root_password"])
            # Validate connection
            _ = sys_db.version()
            return sys_db
        except ArangoError as e:
            print(f"Error: Failed to connect to ArangoDB: {e}", file=sys.stderr)
            return None
        except Exception as e:
            # Handle connection refused, timeout, etc.
            error_msg = str(e)
            if "Connection refused" in error_msg or "NewConnectionError" in error_msg:
                print(f"Error: Cannot connect to ArangoDB at {credentials.get('url', 'unknown')}", file=sys.stderr)
                print("Hint: Is the ArangoDB server running?", file=sys.stderr)
            elif "timeout" in error_msg.lower():
                print(f"Error: Connection to ArangoDB timed out", file=sys.stderr)
            else:
                print(f"Error: Unexpected error connecting to ArangoDB: {e}", file=sys.stderr)
            return None


def confirm_action(message: str, args: Namespace) -> bool:
    """Prompt user for confirmation unless --yes flag is set.
    
    Args:
        message: Confirmation message to display
        args: Parsed arguments with optional 'yes' attribute
    
    Returns:
        True if user confirms or --yes flag is set, False otherwise
    """
    # Check --yes flag
    if hasattr(args, 'yes') and args.yes:
        return True
    
    # Check environment variable
    if os.getenv("MCP_ARANGODB_ASYNC_CLI_YES") == "1":
        return True
    
    # Interactive prompt
    try:
        response = input(f"{message} [y/N]: ").strip().lower()
        return response in ('y', 'yes')
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled", file=sys.stderr)
        return False


class ResultReporter:
    """Color-coded result reporter for CLI commands."""
    
    def __init__(self, command_name: str, dry_run: bool = False):
        """Initialize result reporter.
        
        Args:
            command_name: Name of the command (e.g., "db add")
            dry_run: Whether this is a dry-run operation
        """
        self.command_name = command_name
        self.dry_run = dry_run
        self.consequences = []
    
    def add(self, consequence_type: ConsequenceType, message: str):
        """Add a consequence to report.

        Args:
            consequence_type: Type of consequence (ADD, REMOVE, etc.)
            message: Description of the consequence
        """
        self.consequences.append((consequence_type, message))

    def report_prompt(self) -> str:
        """Generate confirmation prompt with present-tense consequences.
        
        Uses dimmed colors and present tense labels (e.g., [ADD], [REMOVE])
        to visually indicate pending actions that haven't executed yet.

        Returns:
            Formatted prompt string with color-coded consequences
        """
        if not self.consequences:
            return ""

        lines = ["The following actions will be performed:"]
        for consequence_type, message in self.consequences:
            color = consequence_type.prompt_color.value
            reset = Color.RESET.value
            # Use present tense (prompt_label) for confirmation prompts
            lines.append(f"  {color}[{consequence_type.prompt_label}]{reset} {message}")

        return "\n".join(lines)

    def report_result(self):
        """Print execution results with past-tense consequences.
        
        Uses bright colors and past tense labels (e.g., [ADDED], [REMOVED])
        to indicate completed actions.
        """
        if not self.consequences:
            return

        # Print header
        suffix = " (dry-run)" if self.dry_run else ""
        print(f"{self.command_name}{suffix}:")

        # Print consequences
        for consequence_type, message in self.consequences:
            if self.dry_run:
                # Dry-run: use result color + gray suffix with past tense
                color = consequence_type.result_color.value
                reset = Color.RESET.value
                # Use past tense (result_label) even in dry-run to show what WOULD happen
                print(f"{color}[{consequence_type.result_label} - DRY-RUN]{reset} {message}")
            else:
                # Actual execution: use bright result color with past tense
                color = consequence_type.result_color.value
                reset = Color.RESET.value
                print(f"{color}[{consequence_type.result_label}]{reset} {message}")

        # Print dry-run footer
        if self.dry_run:
            print(f"\n{Color.GRAY.value}No changes made. Remove --dry-run to execute.{Color.RESET.value}")

    def has_consequences(self) -> bool:
        """Check if any consequences have been added.

        Returns:
            True if consequences exist, False otherwise
        """
        return len(self.consequences) > 0

