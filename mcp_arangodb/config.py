"""
ArangoDB MCP Server - Configuration Management

This module handles configuration loading from environment variables and validation.
Supports optional .env file loading and provides secure defaults.

Classes:
- Config - Frozen dataclass for configuration settings

Functions:
- load_config() - Load configuration from environment variables
- validate_config() - Validate and normalize configuration values
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

try:
    # Optional: load .env if present; harmless if missing
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except (ImportError, ModuleNotFoundError):
    # python-dotenv is not installed, which is fine
    pass
except Exception as e:
    # Other errors loading .env file (permissions, syntax, etc.)
    # Log but don't fail - .env is optional
    import logging
    logging.getLogger(__name__).debug(f"Failed to load .env file: {e}")


@dataclass(frozen=True)
class Config:
    arango_url: str
    database: str
    username: str
    password: str
    request_timeout: Optional[float] = 30.0


def load_config() -> Config:
    """
    Load configuration from environment variables.

    ARANGO_URL (default: http://localhost:8529)
    ARANGO_DB (default: _system)
    ARANGO_USERNAME (required, but falls back to 'root')
    ARANGO_PASSWORD (required, but empty string if not provided)
    ARANGO_TIMEOUT_SEC (optional float seconds)
    """
    url = os.getenv("ARANGO_URL", "http://localhost:8529")
    db = os.getenv("ARANGO_DB", "_system")
    user = os.getenv("ARANGO_USERNAME", os.getenv("ARANGO_USER", "root"))
    pwd = os.getenv("ARANGO_PASSWORD", os.getenv("ARANGO_PASS", ""))
    timeout_raw = os.getenv("ARANGO_TIMEOUT_SEC", "30.0")

    try:
        timeout = float(timeout_raw)
    except ValueError:
        timeout = 30.0

    return Config(
        arango_url=url,
        database=db,
        username=user,
        password=pwd,
        request_timeout=timeout,
    )


def validate_config(cfg: Config) -> None:
    """Basic validation and normalization for configuration.

    - Ensures URL and database are non-empty
    - Strips whitespace
    - Normalizes URL without trailing slash
    """
    url = (cfg.arango_url or "").strip()
    db = (cfg.database or "").strip()
    user = (cfg.username or "").strip()

    if not url:
        raise ValueError("ARANGO_URL is required")
    if url.endswith("/"):
        url = url[:-1]
    if not db:
        raise ValueError("ARANGO_DB is required")
    if not user:
        raise ValueError("ARANGO_USERNAME is required (can be 'root' for local dev)")

    # Replace fields if normalized (safe handling for frozen dataclass)
    try:
        object.__setattr__(cfg, "arango_url", url)
        object.__setattr__(cfg, "database", db)
        object.__setattr__(cfg, "username", user)
    except Exception as e:
        raise ValueError(f"Failed to normalize configuration: {e}")
