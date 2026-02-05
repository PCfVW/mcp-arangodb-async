"""Configuration file loader for multi-database support.

This module provides YAML-based configuration loading with backward compatibility
for environment variable-based configuration from v0.4.0.
"""

import os
import yaml
import logging
from typing import Dict, Optional
from pathlib import Path
from .multi_db import DatabaseConfig


class ConfigFileLoader:
    """Load and validate database configurations from YAML and environment variables.
    
    Supports both YAML file configuration (new multi-database mode) and
    environment variable configuration (backward compatibility with v0.4.0).
    """

    # Default config file path when no path is specified
    DEFAULT_CONFIG_PATH = "config/databases.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """Initialize ConfigFileLoader.

        Args:
            config_path: Path to YAML configuration file. If None, uses
                ARANGO_DATABASES_CONFIG_FILE env var or DEFAULT_CONFIG_PATH.
        """
        # Priority: explicit path > env var > default
        if config_path is None:
            config_path = os.getenv("ARANGO_DATABASES_CONFIG_FILE", self.DEFAULT_CONFIG_PATH)
        
        # Always store as absolute path for clear display
        self.config_path = os.path.abspath(config_path)
        self.default_database: Optional[str] = None
        self._databases: Dict[str, DatabaseConfig] = {}
        # Track source of configuration (yaml or env_vars)
        self._loaded_from_yaml: bool = False

    def load(self) -> None:
        """Load configurations from YAML file and environment variables.
        
        Priority:
        1. YAML file (if exists)
        2. Environment variables (backward compatibility)
        
        Raises:
            yaml.YAMLError: If YAML file is invalid
        """
        logger = logging.getLogger("mcp_arangodb_async.config_loader")
        
        if os.path.exists(self.config_path):
            logger.info(f"Loading database configuration from YAML file: {self.config_path}")
            self._load_from_yaml()
            self._loaded_from_yaml = True
            logger.info(f"Loaded {len(self._databases)} database(s) from YAML file")
        else:
            logger.warning(f"YAML config file not found: {self.config_path}")
            logger.info("Falling back to environment variables (v0.4.0 backward compatibility)")
            self._load_from_env_vars()
            self._loaded_from_yaml = False
            logger.info(f"Loaded {len(self._databases)} database(s) from environment variables")

    def load_yaml_only(self) -> None:
        """Load configurations from YAML file only (no env var fallback).
        
        Use this method when you need to manage the config file directly
        (e.g., adding/removing entries) without merging with environment
        variable defaults.
        
        Raises:
            yaml.YAMLError: If YAML file is invalid
        """
        if os.path.exists(self.config_path):
            self._load_from_yaml()
            self._loaded_from_yaml = True
        else:
            # No file exists - start with empty config
            self._databases = {}
            self.default_database = None
            self._loaded_from_yaml = False

    @property
    def loaded_from_yaml(self) -> bool:
        """Check if configuration was loaded from YAML file.
        
        Returns:
            True if loaded from YAML file, False if from environment variables
        """
        return self._loaded_from_yaml

    def _load_from_yaml(self) -> None:
        """Load configuration from YAML file.
        
        Raises:
            yaml.YAMLError: If YAML file is invalid
        """
        logger = logging.getLogger("mcp_arangodb_async.config_loader")
        
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Handle empty YAML file
        if config is None:
            config = {}
            logger.warning("YAML file is empty, no databases configured")
        
        # Load default database
        self.default_database = config.get("default_database")
        if self.default_database:
            logger.info(f"Default database from YAML: '{self.default_database}'")
        else:
            logger.info("No default database specified in YAML (will use fallback resolution)")
        
        # Load database configurations
        databases = config.get("databases", {})
        for key, db_config in databases.items():
            self._databases[key] = DatabaseConfig(**db_config)
            logger.debug(f"  - Registered database '{key}': {db_config.get('database')}@{db_config.get('url')}")

    def _load_from_env_vars(self) -> None:
        """Load configuration from environment variables (backward compatibility).
        
        Supports v0.4.0 environment variables:
        - ARANGO_URL (default: http://localhost:8529)
        - ARANGO_DB (default: _system)
        - ARANGO_USERNAME (default: root)
        - ARANGO_PASSWORD (password environment variable)
        """
        logger = logging.getLogger("mcp_arangodb_async.config_loader")
        
        url = os.getenv("ARANGO_URL", "http://localhost:8529")
        database = os.getenv("ARANGO_DB", "_system")
        username = os.getenv("ARANGO_USERNAME", "root")
        timeout = float(os.getenv("ARANGO_TIMEOUT_SEC", "30.0"))
        
        logger.info(f"Environment variables: ARANGO_URL={url}, ARANGO_DB={database}, ARANGO_USERNAME={username}")
        
        self._databases["default"] = DatabaseConfig(
            url=url,
            database=database,
            username=username,
            password_env="ARANGO_PASSWORD",
            timeout=timeout
        )
        self.default_database = "default"
        logger.info("Created single 'default' database configuration from environment variables")

    def get_configured_databases(self) -> Dict[str, DatabaseConfig]:
        """Get all configured databases.
        
        Returns:
            Dictionary mapping database keys to their configurations
        """
        return self._databases.copy()

    def add_database(self, database_key: str, config: DatabaseConfig) -> None:
        """Add a database configuration.
        
        Args:
            database_key: Unique identifier for this database
            config: Database configuration
        """
        self._databases[database_key] = config

    def remove_database(self, database_key: str) -> None:
        """Remove a database configuration.
        
        Args:
            database_key: Database identifier to remove
        """
        self._databases.pop(database_key, None)

    def save_to_yaml(self) -> None:
        """Save current configuration to YAML file.
        
        Creates parent directories if they don't exist.
        """
        # Create parent directory if it doesn't exist
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        # Build configuration dictionary
        config_data = {}
        
        if self.default_database:
            config_data["default_database"] = self.default_database
        
        # Convert DatabaseConfig objects to dictionaries
        databases = {}
        for key, db_config in self._databases.items():
            databases[key] = {
                "url": db_config.url,
                "database": db_config.database,
                "username": db_config.username,
                "password_env": db_config.password_env,
                "timeout": db_config.timeout
            }
            if db_config.description:
                databases[key]["description"] = db_config.description
        
        config_data["databases"] = databases
        
        # Write to YAML file
        with open(self.config_path, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

