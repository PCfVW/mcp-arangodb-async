"""
ArangoDB MCP Server - Database Connection Utilities

This module provides database connection management with retry logic and health checks.
Handles ArangoDB client creation, connection validation, and error recovery.

Functions:
- get_client_and_db() - Create ArangoDB client and database connection
- health_check() - Perform database health check
- connect_with_retry() - Connect with configurable retry logic
"""

from __future__ import annotations

import asyncio
import logging
import threading
from typing import Optional, Tuple
from arango import ArangoClient
from arango.database import StandardDatabase

from .config import Config


class ConnectionManager:
    """Thread-safe singleton connection manager for ArangoDB connections."""

    _instance: Optional['ConnectionManager'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'ConnectionManager':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._client = None
                    cls._instance._db = None
                    cls._instance._config = None
        return cls._instance

    def get_connection(self, cfg: Config) -> Tuple[ArangoClient, StandardDatabase]:
        """Get or create a connection to ArangoDB.

        Reuses existing connection if configuration matches, otherwise creates new one.
        """
        with self._lock:
            # Check if we need to create a new connection
            if (self._client is None or self._db is None or
                self._config is None or not self._config_matches(cfg)):

                # Close existing connection if any
                if self._client is not None:
                    try:
                        self._client.close()
                    except Exception:
                        pass  # Ignore cleanup errors

                # Create new connection
                self._client = ArangoClient(
                    hosts=cfg.arango_url,
                    request_timeout=cfg.request_timeout
                )
                self._db = self._client.db(
                    cfg.database,
                    username=cfg.username,
                    password=cfg.password
                )

                # Validate connection
                _ = self._db.version()
                self._config = cfg

            return self._client, self._db

    def _config_matches(self, cfg: Config) -> bool:
        """Check if the current configuration matches the provided one."""
        if self._config is None:
            return False
        return (
            self._config.arango_url == cfg.arango_url and
            self._config.database == cfg.database and
            self._config.username == cfg.username and
            self._config.password == cfg.password and
            self._config.request_timeout == cfg.request_timeout
        )

    def close(self):
        """Close the current connection."""
        with self._lock:
            if self._client is not None:
                try:
                    self._client.close()
                except Exception:
                    pass  # Ignore cleanup errors
                finally:
                    self._client = None
                    self._db = None
                    self._config = None


# Global connection manager instance
_connection_manager = ConnectionManager()


def get_client_and_db(cfg: Config):
    """Create an ArangoDB client and DB handle using the given Config.

    Returns a tuple (client, db). Raises on connection/auth errors.

    Note: This function now uses connection pooling for better performance.
    """
    return _connection_manager.get_connection(cfg)


def get_client_and_db_new_connection(cfg: Config):
    """Create a new ArangoDB client and DB handle, bypassing connection pooling.

    Use this when you specifically need a fresh connection.
    Returns a tuple (client, db). Raises on connection/auth errors.
    """
    client = ArangoClient(hosts=cfg.arango_url, request_timeout=cfg.request_timeout)
    db = client.db(cfg.database, username=cfg.username, password=cfg.password)
    # Perform a lightweight call to validate credentials and connectivity
    _ = db.version()
    return client, db


def close_connections():
    """Close all pooled connections. Useful for cleanup."""
    _connection_manager.close()


def health_check(db) -> dict:
    """Return a small health report by querying DB version.

    Raises underlying exceptions if not reachable.
    """
    ver = db.version()
    return {"version": ver}


async def connect_with_retry(
    cfg: Config,
    retries: int = 3,
    delay_sec: float = 1.0,
    logger: Optional[object] = None,
):
    """Attempt to connect and validate with configurable retries.

    Returns (client, db) on success; (None, None) on final failure.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(1, max(1, retries) + 1):
        try:
            client, db = get_client_and_db(cfg)
            if logger:
                try:
                    logger.info(
                        "Connected to ArangoDB at %s db=%s (attempt %d)",
                        cfg.arango_url,
                        cfg.database,
                        attempt,
                    )
                except Exception:
                    pass
            return client, db
        except Exception as e:
            last_exc = e
            if logger:
                try:
                    logger.warning("ArangoDB connection attempt %d failed", attempt, exc_info=True)
                except Exception:
                    pass
            if attempt < retries:
                try:
                    await asyncio.sleep(delay_sec)
                except Exception:
                    pass
    if logger:
        try:
            logger.error(
                "Failed to connect to ArangoDB after %d attempts; continuing without DB",
                retries,
            )
        except Exception:
            pass
    return None, None
