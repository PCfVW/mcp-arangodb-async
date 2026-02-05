"""
Transport Configuration for MCP ArangoDB Server

This module defines configuration for different MCP transport types (stdio, HTTP).
Provides validation and default values for transport-specific settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TransportConfig:
    """Configuration for MCP server transport.
    
    Attributes:
        transport: Transport type ("stdio" or "http")
        http_host: Host address for HTTP transport (default: "0.0.0.0")
        http_port: Port number for HTTP transport (default: 8000)
        http_stateless: Whether to run HTTP in stateless mode (default: False)
        http_cors_origins: List of allowed CORS origins (default: ["*"])
    """
    
    transport: Literal["stdio", "http"] = "stdio"
    http_host: str = "0.0.0.0"
    http_port: int = 8000
    http_stateless: bool = False
    http_cors_origins: list[str] | None = None
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate transport type
        if self.transport not in ("stdio", "http"):
            raise ValueError(f"Invalid transport: {self.transport}. Must be 'stdio' or 'http'.")
        
        # Validate HTTP port
        if not (1 <= self.http_port <= 65535):
            raise ValueError(f"Invalid HTTP port: {self.http_port}. Must be between 1 and 65535.")
        
        # Set default CORS origins if None
        if self.http_cors_origins is None:
            # Use object.__setattr__ because dataclass is frozen
            object.__setattr__(self, "http_cors_origins", ["*"])

