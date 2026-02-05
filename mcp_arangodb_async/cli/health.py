"""CLI handlers for health and version commands.

This module provides command-line interface for health checks and version display.
Follows the handle_XXX pattern used by other CLI modules.

Functions:
- handle_health() - Run health check and output JSON
- handle_version() - Display version information
"""

from __future__ import annotations

import json
import logging
import sys
import time
import warnings
from argparse import Namespace
from typing import Any, Dict, Optional, Tuple

from arango import ArangoClient
from arango.database import StandardDatabase

from .utils import EXIT_SUCCESS, EXIT_ERROR


def _suppress_connection_warnings() -> None:
    """Suppress urllib3 connection warnings for cleaner CLI output."""
    logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    warnings.filterwarnings("ignore", category=Warning, module="urllib3")


def _get_connection_error_message(error: Exception, url: str) -> str:
    """Convert connection exception to user-friendly message.
    
    Args:
        error: The exception that occurred
        url: The ArangoDB URL being connected to
        
    Returns:
        User-friendly error message string
    """
    error_msg = str(error)
    
    if "Connection refused" in error_msg or "NewConnectionError" in error_msg:
        return f"Cannot connect to ArangoDB at {url}. Is the server running?"
    elif "ConnectionAbortedError" in error_msg or "Can't connect to host" in error_msg:
        return f"Connection to ArangoDB at {url} failed. Check server status."
    elif "timeout" in error_msg.lower():
        return f"Connection to ArangoDB at {url} timed out."
    elif "401" in error_msg or "Unauthorized" in error_msg:
        return f"Authentication failed. Check username and password."
    elif "403" in error_msg or "Forbidden" in error_msg:
        return f"Access denied. Check user permissions."
    else:
        return f"Connection failed: {error_msg}"


def _connect_with_progress(
    url: str,
    database: str,
    username: str,
    password: str,
    timeout: float,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> Tuple[Optional[ArangoClient], Optional[StandardDatabase], Optional[str]]:
    """Attempt connection with user-friendly progress feedback.
    
    Args:
        url: ArangoDB server URL
        database: Database name
        username: Username for authentication
        password: Password for authentication
        timeout: Connection timeout in seconds
        max_retries: Maximum number of connection attempts
        retry_delay: Delay between retries in seconds
        
    Returns:
        Tuple of (client, db, error_message). On success, error_message is None.
        On failure, client and db are None and error_message contains the reason.
    """
    last_error: Optional[Exception] = None
    client: Optional[ArangoClient] = None
    
    for attempt in range(1, max_retries + 1):
        try:
            # Show progress to user
            if attempt == 1:
                print(f"Connecting to ArangoDB at {url}...", file=sys.stderr)
            else:
                print(f"  Retry {attempt}/{max_retries}...", file=sys.stderr)
            
            # Create client with minimal internal retries (we handle retries ourselves)
            client = ArangoClient(
                hosts=url,
                request_timeout=timeout,
                resolver_max_tries=1,  # Disable internal retries
            )
            db = client.db(database, username=username, password=password)
            
            # Validate connection
            _ = db.version()
            
            # Success!
            print(f"  Connected successfully.", file=sys.stderr)
            return client, db, None
            
        except Exception as e:
            last_error = e
            
            # Close failed client
            if client is not None:
                try:
                    client.close()
                except Exception:
                    pass
                client = None
            
            # Don't retry on auth errors - they won't succeed
            error_str = str(e)
            if "401" in error_str or "Unauthorized" in error_str:
                break
            if "403" in error_str or "Forbidden" in error_str:
                break
                
            # Wait before retry (except on last attempt)
            if attempt < max_retries:
                print(f"  Connection failed, waiting {retry_delay}s before retry...", file=sys.stderr)
                time.sleep(retry_delay)
    
    # All retries exhausted
    error_message = _get_connection_error_message(last_error, url) if last_error else "Unknown error"
    return None, None, error_message


def handle_health(args: Namespace) -> int:
    """Run health check and output JSON result.
    
    Performs a connectivity test to ArangoDB and outputs structured JSON
    with status information. Designed for monitoring and automation.
    
    Progress messages are printed to stderr so JSON output remains clean on stdout.
    
    Args:
        args: Parsed command-line arguments (not currently used)
        
    Returns:
        Exit code: 0 for healthy, 1 for unhealthy/error
    """
    # Suppress urllib3 warnings before any connection attempt
    _suppress_connection_warnings()
    
    from .config import load_config
    
    cfg = load_config()
    
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=Warning, module="urllib3")
        
        # Use our custom retry with progress feedback
        client, db, error_message = _connect_with_progress(
            url=cfg.arango_url,
            database=cfg.database,
            username=cfg.username,
            password=cfg.password,
            timeout=cfg.request_timeout,
            max_retries=3,
            retry_delay=2.0,
        )
        
        if client is not None and db is not None:
            try:
                # Connection successful - get version info
                version = db.version()
                
                result: Dict[str, Any] = {
                    "ok": True,
                    "status": "healthy",
                    "url": cfg.arango_url,
                    "database": cfg.database,
                    "username": cfg.username,
                    "info": {
                        "version": version,
                    }
                }
                
                print(json.dumps(result, ensure_ascii=False, indent=2))
                return EXIT_SUCCESS
                
            finally:
                try:
                    client.close()
                except Exception:
                    pass
        else:
            # Connection failed
            result = {
                "ok": False,
                "status": "unhealthy",
                "url": cfg.arango_url,
                "database": cfg.database,
                "username": cfg.username,
                "error": error_message or "Unknown connection error",
            }
            
            print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
            return EXIT_ERROR


def handle_version(args: Namespace) -> int:
    """Display version information.
    
    Shows the package version and Python version.
    
    Args:
        args: Parsed command-line arguments (not currently used)
        
    Returns:
        Exit code: 0 for success, 1 for error
    """
    try:
        from importlib.metadata import version
        pkg_version = version("mcp-arangodb-async")
    except Exception:
        pkg_version = "unknown"
    
    print(f"mcp-arangodb-async version {pkg_version}")
    print(f"Python {sys.version.split()[0]}")
    return EXIT_SUCCESS
