"""
ArangoDB MCP Server - MCP Content Converter

This module provides optional conversion utilities for transforming handler Dict results
into MCP TextContent format with multiple formatting options. Users can choose to convert
handler results or use them directly as Python dictionaries.

Classes:
- MCPContentConverter - Main converter class with multiple format options
- Pre-configured converter instances for common use cases

Functions:
- create_converter() - Factory function for creating converters with presets
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal, Union, Tuple
import json
from datetime import datetime

try:
    import mcp.types as types
except ImportError:
    # Fallback for testing or when MCP not available
    class types:
        class TextContent:
            def __init__(self, type: str, text: str):
                self.type = type
                self.text = text


class MCPContentConverter:
    """Optional converter for transforming handler Dict results to MCP TextContent format.
    
    Provides multiple formatting options while maintaining backward compatibility.
    Users can choose to convert handler results or use them directly as Python dicts.
    """
    
    def __init__(self, 
                 indent: Optional[int] = None,
                 ensure_ascii: bool = False,
                 sort_keys: bool = False,
                 include_timestamps: bool = False):
        """Initialize converter with formatting preferences.
        
        Args:
            indent: JSON indentation level (None for compact)
            ensure_ascii: Whether to escape non-ASCII characters
            sort_keys: Whether to sort dictionary keys
            include_timestamps: Whether to add timestamp metadata
        """
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.sort_keys = sort_keys
        self.include_timestamps = include_timestamps
    
    def to_text_content(self, data: Any, 
                       format_style: Literal["json", "markdown", "yaml", "table"] = "json",
                       title: Optional[str] = None) -> List[types.TextContent]:
        """Convert handler result to MCP TextContent format.
        
        Args:
            data: Handler result (typically Dict[str, Any])
            format_style: Output format preference
            title: Optional title for formatted output
            
        Returns:
            List[types.TextContent] compatible with MCP protocol
        """
        
        if format_style == "json":
            text = self._format_as_json(data)
        elif format_style == "markdown":
            text = self._format_as_markdown(data, title)
        elif format_style == "yaml":
            text = self._format_as_yaml(data)
        elif format_style == "table":
            text = self._format_as_table(data)
        else:
            text = str(data)
        
        # Add timestamp if requested
        if self.include_timestamps:
            timestamp = datetime.now().isoformat()
            text = f"<!-- Generated: {timestamp} -->\n{text}"
        
        return [types.TextContent(type="text", text=text)]
    
    def to_structured_content(self, data: Any) -> Dict[str, Any]:
        """Convert data to structured format for MCP 2025-06-18+ clients.
        
        Args:
            data: Handler result
            
        Returns:
            Structured data dictionary
        """
        return self._serialize_for_json(data)
    
    def to_mixed_content(self, data: Any, summary: str, 
                        title: Optional[str] = None) -> Tuple[List[types.TextContent], Dict[str, Any]]:
        """Return both human-readable and structured content.
        
        Args:
            data: Handler result
            summary: Human-readable summary text
            title: Optional title
            
        Returns:
            Tuple of (TextContent list, structured data dict)
        """
        text_content = [types.TextContent(type="text", text=summary)]
        if title:
            text_content[0].text = f"# {title}\n\n{summary}"
        
        structured_data = self.to_structured_content(data)
        return text_content, structured_data
    
    def _format_as_json(self, data: Any) -> str:
        """Format data as JSON with configured options."""
        return json.dumps(
            self._serialize_for_json(data),
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            sort_keys=self.sort_keys
        )
    
    def _format_as_markdown(self, data: Any, title: Optional[str] = None) -> str:
        """Format data as Markdown with proper structure."""
        parts = []
        
        if title:
            parts.append(f"# {title}")
        
        # Handle error responses specially
        if isinstance(data, dict) and "error" in data:
            error_type = data.get("type", "Unknown")
            error_msg = data["error"]
            return f"## ❌ Error: {error_type}\n\n{error_msg}"
        
        # Format regular data
        if isinstance(data, dict):
            for key, value in data.items():
                section_title = key.replace('_', ' ').title()
                
                if isinstance(value, list) and value:
                    parts.append(f"## {section_title}")
                    if isinstance(value[0], dict):
                        # Format as table if list of dicts
                        parts.append(self._dict_list_to_markdown_table(value))
                    else:
                        # Format as bullet list
                        bullet_items = [f"- {item}" for item in value]
                        parts.append("\n".join(bullet_items))
                        
                elif isinstance(value, dict):
                    parts.append(f"## {section_title}")
                    parts.append(f"```json\n{json.dumps(value, indent=2)}\n```")
                    
                else:
                    parts.append(f"**{section_title}:** {value}")
        
        elif isinstance(data, list):
            if title:
                parts.append(f"## {title}")
            if data and isinstance(data[0], dict):
                parts.append(self._dict_list_to_markdown_table(data))
            else:
                bullet_items = [f"- {item}" for item in data]
                parts.append("\n".join(bullet_items))
        
        return "\n\n".join(parts)
    
    def _format_as_yaml(self, data: Any) -> str:
        """Format data as YAML (requires PyYAML dependency)."""
        try:
            import yaml
            return yaml.dump(
                self._serialize_for_json(data),
                default_flow_style=False,
                sort_keys=self.sort_keys,
                allow_unicode=not self.ensure_ascii
            )
        except ImportError:
            # Fallback to JSON if PyYAML not available
            return f"# YAML formatting requires PyYAML\n# Falling back to JSON:\n\n{self._format_as_json(data)}"
    
    def _format_as_table(self, data: Any) -> str:
        """Format data as ASCII table (requires tabulate dependency)."""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            try:
                import tabulate
                return tabulate.tabulate(data, headers="keys", tablefmt="grid")
            except ImportError:
                return f"# Table formatting requires tabulate\n# Falling back to JSON:\n\n{self._format_as_json(data)}"
        
        # Not suitable for table format
        return self._format_as_json(data)
    
    def _dict_list_to_markdown_table(self, data: List[Dict]) -> str:
        """Convert list of dicts to Markdown table."""
        if not data:
            return "*(No data)*"
        
        # Get all unique keys
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        
        headers = sorted(all_keys)
        
        # Create table
        header_row = "| " + " | ".join(headers) + " |"
        separator = "| " + " | ".join(["---"] * len(headers)) + " |"
        
        rows = []
        for item in data:
            row_values = []
            for header in headers:
                value = item.get(header, "")
                # Truncate long values
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                elif isinstance(value, (dict, list)):
                    value = f"{type(value).__name__}({len(value)})"
                row_values.append(str(value))
            
            rows.append("| " + " | ".join(row_values) + " |")
        
        return "\n".join([header_row, separator] + rows)
    
    def _serialize_for_json(self, data: Any) -> Any:
        """Serialize data for JSON output, handling special types."""
        if isinstance(data, datetime):
            return data.isoformat()
        elif hasattr(data, '__dict__'):
            return self._serialize_for_json(data.__dict__)
        elif isinstance(data, dict):
            return {k: self._serialize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_for_json(item) for item in data]
        elif hasattr(data, 'isoformat'):  # datetime-like objects
            return str(data)
        return data


# Pre-configured converters for common use cases
DEFAULT_CONVERTER = MCPContentConverter()
PRETTY_CONVERTER = MCPContentConverter(indent=2, sort_keys=True)
MARKDOWN_CONVERTER = MCPContentConverter(indent=2, include_timestamps=True)
COMPACT_CONVERTER = MCPContentConverter(ensure_ascii=True, sort_keys=False)


def create_converter(format_style: str = "json", 
                    pretty: bool = False,
                    include_timestamps: bool = False) -> MCPContentConverter:
    """Create converter with common presets.
    
    Args:
        format_style: Default format preference
        pretty: Whether to use pretty formatting
        include_timestamps: Whether to include timestamp metadata
        
    Returns:
        Configured MCPContentConverter instance
    """
    return MCPContentConverter(
        indent=2 if pretty else None,
        sort_keys=pretty,
        include_timestamps=include_timestamps
    )
