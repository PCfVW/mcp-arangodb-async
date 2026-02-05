"""Session state management for multi-tenancy support.

This module provides per-session state isolation for focused database context,
active workflow, tool lifecycle stage, and tool usage tracking.
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional, Any


class SessionState:
    """Manages per-session state for multi-database workflows.
    
    Provides isolation boundary for different agents (sessions) to work with
    different databases and workflow stages without interference.
    
    Thread-safe using asyncio.Lock for state mutations.
    """

    def __init__(self):
        """Initialize SessionState with empty state dictionaries."""
        self._focused_database: Dict[str, Optional[str]] = {}
        self._active_workflow: Dict[str, str] = {}
        self._tool_lifecycle_stage: Dict[str, str] = {}
        self._tool_usage_stats: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    def initialize_session(self, session_id: str) -> None:
        """Initialize new session with default values.
        
        Args:
            session_id: Unique session identifier
        """
        self._focused_database[session_id] = None
        self._active_workflow[session_id] = "baseline"
        self._tool_lifecycle_stage[session_id] = "setup"
        self._tool_usage_stats[session_id] = {}

    def has_session(self, session_id: str) -> bool:
        """Check if session exists.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if session exists, False otherwise
        """
        return session_id in self._focused_database

    async def set_focused_database(self, session_id: str, database_key: Optional[str]) -> None:
        """Set focused database for session (async-safe).

        Args:
            session_id: Unique session identifier
            database_key: Database key to focus on, or None to unset the focused database
        """
        async with self._lock:
            self._focused_database[session_id] = database_key

    def get_focused_database(self, session_id: str) -> Optional[str]:
        """Get focused database for session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Database key or None if not set
        """
        return self._focused_database.get(session_id)

    async def set_active_workflow(self, session_id: str, workflow: str) -> None:
        """Set active workflow for session (async-safe).
        
        Args:
            session_id: Unique session identifier
            workflow: Workflow name (e.g., "baseline", "data_migration")
        """
        async with self._lock:
            self._active_workflow[session_id] = workflow

    def get_active_workflow(self, session_id: str) -> Optional[str]:
        """Get active workflow for session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Workflow name or None if session doesn't exist
        """
        return self._active_workflow.get(session_id)

    async def set_tool_lifecycle_stage(self, session_id: str, stage: str) -> None:
        """Set tool lifecycle stage for session (async-safe).
        
        Args:
            session_id: Unique session identifier
            stage: Lifecycle stage (e.g., "setup", "data_loading", "analysis")
        """
        async with self._lock:
            self._tool_lifecycle_stage[session_id] = stage

    def get_tool_lifecycle_stage(self, session_id: str) -> Optional[str]:
        """Get tool lifecycle stage for session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Lifecycle stage or None if session doesn't exist
        """
        return self._tool_lifecycle_stage.get(session_id)

    def track_tool_usage(self, session_id: str, tool_name: str) -> None:
        """Track tool usage for session.
        
        Args:
            session_id: Unique session identifier
            tool_name: Name of the tool being used
        """
        if session_id not in self._tool_usage_stats:
            self._tool_usage_stats[session_id] = {}
        
        session_stats = self._tool_usage_stats[session_id]
        
        if tool_name not in session_stats:
            session_stats[tool_name] = {
                "first_used": datetime.now().isoformat(),
                "last_used": datetime.now().isoformat(),
                "use_count": 1
            }
        else:
            session_stats[tool_name]["last_used"] = datetime.now().isoformat()
            session_stats[tool_name]["use_count"] += 1

    def get_tool_usage_stats(self, session_id: str) -> Dict[str, Any]:
        """Get tool usage statistics for session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Dictionary of tool usage statistics
        """
        return self._tool_usage_stats.get(session_id, {})

    def cleanup_session(self, session_id: str) -> None:
        """Clean up session state on client disconnect.
        
        Args:
            session_id: Unique session identifier
        """
        self._focused_database.pop(session_id, None)
        self._active_workflow.pop(session_id, None)
        self._tool_lifecycle_stage.pop(session_id, None)
        self._tool_usage_stats.pop(session_id, None)

    def cleanup_all(self) -> None:
        """Clean up all session state."""
        self._focused_database.clear()
        self._active_workflow.clear()
        self._tool_lifecycle_stage.clear()
        self._tool_usage_stats.clear()

