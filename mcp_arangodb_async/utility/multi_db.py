"""Multi-database connection manager for multi-tenancy support.

This module provides connection pooling for multiple ArangoDB servers and databases,
enabling a single MCP server instance to manage connections to multiple databases.
"""

import asyncio
import os
from typing import Dict, Tuple, Any, Optional
from dataclasses import dataclass
from arango import ArangoClient
from arango.database import StandardDatabase


@dataclass
class DatabaseConfig:
    """Configuration for a single database connection."""
    
    url: str
    database: str
    username: str
    password_env: str
    timeout: float = 30.0
    description: Optional[str] = None


class MultiDatabaseConnectionManager:
    """Manages connections to multiple ArangoDB servers and databases.
    
    Provides connection pooling with async-safe access for multi-database workflows.
    Connections are created lazily on first access and reused for subsequent requests.
    
    Thread-safe using asyncio.Lock for connection pool mutations.
    """

    def __init__(self):
        """Initialize MultiDatabaseConnectionManager with empty pools."""
        self._pools: Dict[str, Tuple[ArangoClient, StandardDatabase]] = {}
        self._configs: Dict[str, DatabaseConfig] = {}
        self._lock = asyncio.Lock()

    async def initialize(self) -> None:
        """Initialize connection manager.
        
        This method is called during server startup to prepare the manager.
        Actual connections are created lazily on first access.
        """
        # No pre-connection needed - connections are created on demand
        pass

    async def get_connection(self, database_key: str) -> Tuple[ArangoClient, StandardDatabase]:
        """Get or create connection for specified database (async-safe).
        
        Args:
            database_key: Database identifier from configuration
            
        Returns:
            Tuple of (ArangoClient, StandardDatabase)
            
        Raises:
            KeyError: If database_key is not registered
        """
        # Fast path: connection already exists
        if database_key in self._pools:
            return self._pools[database_key]
        
        # Slow path: create new connection (async-safe)
        async with self._lock:
            # Double-check after acquiring lock
            if database_key in self._pools:
                return self._pools[database_key]
            
            # Get configuration
            if database_key not in self._configs:
                raise KeyError(f"Database '{database_key}' not registered")
            
            config = self._configs[database_key]
            
            # Create connection
            client = ArangoClient(
                hosts=config.url,
                request_timeout=config.timeout
            )
            
            # Get password from environment variable
            password = os.getenv(config.password_env, "")
            
            db = client.db(
                config.database,
                username=config.username,
                password=password
            )
            
            # Store in pool
            self._pools[database_key] = (client, db)
            
            return self._pools[database_key]

    def get_configured_databases(self) -> Dict[str, DatabaseConfig]:
        """Get all configured databases.
        
        Returns:
            Dictionary mapping database keys to their configurations
        """
        return self._configs.copy()

    async def test_connection(self, database_key: str) -> Dict[str, Any]:
        """Test connection to a specific database.
        
        Args:
            database_key: Database identifier from configuration
            
        Returns:
            Dictionary with connection status and version info
        """
        try:
            client, db = await self.get_connection(database_key)
            version = db.version()
            return {
                "connected": True,
                "version": version
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }

    def register_database(self, database_key: str, config: DatabaseConfig) -> None:
        """Register a new database configuration.
        
        Args:
            database_key: Unique identifier for this database
            config: Database configuration
        """
        self._configs[database_key] = config

    async def close_all(self) -> None:
        """Close all connections in the pool.
        
        Called during server shutdown to cleanup resources.
        """
        async with self._lock:
            for database_key, (client, db) in self._pools.items():
                try:
                    client.close()
                except Exception:
                    # Ignore errors during cleanup
                    pass
            
            self._pools.clear()

