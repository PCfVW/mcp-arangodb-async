"""Unit tests for MCP content converter."""

import json
import pytest
from datetime import datetime
from unittest.mock import patch

from mcp_arangodb_async.content_converter import (
    MCPContentConverter,
    DEFAULT_CONVERTER,
    PRETTY_CONVERTER,
    MARKDOWN_CONVERTER,
    COMPACT_CONVERTER,
    create_converter,
)


class TestMCPContentConverter:
    """Test cases for MCPContentConverter class."""

    def test_init_default(self):
        """Test converter initialization with defaults."""
        converter = MCPContentConverter()
        assert converter.indent is None
        assert converter.ensure_ascii is False
        assert converter.sort_keys is False
        assert converter.include_timestamps is False

    def test_init_custom(self):
        """Test converter initialization with custom settings."""
        converter = MCPContentConverter(
            indent=4,
            ensure_ascii=True,
            sort_keys=True,
            include_timestamps=True
        )
        assert converter.indent == 4
        assert converter.ensure_ascii is True
        assert converter.sort_keys is True
        assert converter.include_timestamps is True

    def test_to_text_content_json_format(self):
        """Test JSON formatting."""
        converter = MCPContentConverter(indent=2)
        data = {"name": "test", "count": 42}
        
        result = converter.to_text_content(data, format_style="json")
        
        assert len(result) == 1
        assert result[0].type == "text"
        
        # Parse the JSON to verify it's valid
        parsed = json.loads(result[0].text)
        assert parsed["name"] == "test"
        assert parsed["count"] == 42

    def test_to_text_content_markdown_format(self):
        """Test Markdown formatting."""
        converter = MCPContentConverter()
        data = {
            "graph_name": "test_graph",
            "total_vertices": 100,
            "statistics": [{"name": "graph1", "edges": 50}]
        }
        
        result = converter.to_text_content(data, format_style="markdown", title="Graph Report")
        
        assert len(result) == 1
        assert result[0].type == "text"
        text = result[0].text
        
        assert "# Graph Report" in text
        assert "**Graph Name:** test_graph" in text
        assert "**Total Vertices:** 100" in text
        assert "## Statistics" in text

    def test_to_text_content_error_format(self):
        """Test error response formatting."""
        converter = MCPContentConverter()
        error_data = {
            "error": "Graph not found",
            "type": "GraphNotFound"
        }
        
        result = converter.to_text_content(error_data, format_style="markdown")
        
        assert len(result) == 1
        text = result[0].text
        assert "## ❌ Error: GraphNotFound" in text
        assert "Graph not found" in text

    def test_to_text_content_yaml_format(self):
        """Test YAML formatting with PyYAML available."""
        converter = MCPContentConverter()
        data = {"name": "test", "items": ["a", "b", "c"]}
        
        with patch('yaml.dump') as mock_yaml_dump:
            mock_yaml_dump.return_value = "name: test\nitems:\n- a\n- b\n- c\n"
            
            result = converter.to_text_content(data, format_style="yaml")
            
            assert len(result) == 1
            assert "name: test" in result[0].text
            mock_yaml_dump.assert_called_once()

    def test_to_text_content_yaml_format_fallback(self):
        """Test YAML formatting fallback when PyYAML not available."""
        converter = MCPContentConverter()
        data = {"name": "test"}
        
        with patch('builtins.__import__', side_effect=ImportError):
            result = converter.to_text_content(data, format_style="yaml")
            
            assert len(result) == 1
            text = result[0].text
            assert "YAML formatting requires PyYAML" in text
            assert "Falling back to JSON" in text

    def test_to_text_content_table_format(self):
        """Test table formatting with tabulate available."""
        converter = MCPContentConverter()
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        
        with patch('tabulate.tabulate') as mock_tabulate:
            mock_tabulate.return_value = "| name  | age |\n|-------|-----|\n| Alice |  30 |\n| Bob   |  25 |"
            
            result = converter.to_text_content(data, format_style="table")
            
            assert len(result) == 1
            assert "Alice" in result[0].text
            mock_tabulate.assert_called_once_with(data, headers="keys", tablefmt="grid")

    def test_to_text_content_table_format_fallback(self):
        """Test table formatting fallback when tabulate not available."""
        converter = MCPContentConverter()
        data = [{"name": "test"}]
        
        with patch('builtins.__import__', side_effect=ImportError):
            result = converter.to_text_content(data, format_style="table")
            
            assert len(result) == 1
            text = result[0].text
            assert "Table formatting requires tabulate" in text
            assert "Falling back to JSON" in text

    def test_to_text_content_with_timestamps(self):
        """Test content generation with timestamps."""
        converter = MCPContentConverter(include_timestamps=True)
        data = {"test": "data"}
        
        result = converter.to_text_content(data)
        
        assert len(result) == 1
        text = result[0].text
        assert "<!-- Generated:" in text
        assert '"test": "data"' in text

    def test_to_structured_content(self):
        """Test structured content conversion."""
        converter = MCPContentConverter()
        data = {"name": "test", "timestamp": datetime(2024, 1, 1, 12, 0, 0)}
        
        result = converter.to_structured_content(data)
        
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["timestamp"] == "2024-01-01T12:00:00"  # ISO format

    def test_to_mixed_content(self):
        """Test mixed content generation."""
        converter = MCPContentConverter()
        data = {"count": 42}
        summary = "Operation completed successfully"
        
        text_content, structured_data = converter.to_mixed_content(data, summary, "Report")
        
        assert len(text_content) == 1
        assert text_content[0].type == "text"
        assert "# Report" in text_content[0].text
        assert "Operation completed successfully" in text_content[0].text
        
        assert isinstance(structured_data, dict)
        assert structured_data["count"] == 42

    def test_dict_list_to_markdown_table(self):
        """Test conversion of list of dicts to Markdown table."""
        converter = MCPContentConverter()
        data = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "San Francisco"}
        ]
        
        result = converter._dict_list_to_markdown_table(data)
        
        assert "| age | city | name |" in result
        assert "| --- | --- | --- |" in result
        assert "| 30 | New York | Alice |" in result
        assert "| 25 | San Francisco | Bob |" in result

    def test_dict_list_to_markdown_table_empty(self):
        """Test conversion of empty list to Markdown table."""
        converter = MCPContentConverter()
        
        result = converter._dict_list_to_markdown_table([])
        
        assert result == "*(No data)*"

    def test_dict_list_to_markdown_table_truncation(self):
        """Test long value truncation in Markdown table."""
        converter = MCPContentConverter()
        long_text = "a" * 60  # Longer than 50 character limit
        data = [{"name": "test", "description": long_text}]
        
        result = converter._dict_list_to_markdown_table(data)
        
        assert "..." in result  # Truncation indicator
        assert len([line for line in result.split('\n') if long_text[:47] in line]) > 0

    def test_serialize_for_json_datetime(self):
        """Test JSON serialization of datetime objects."""
        converter = MCPContentConverter()
        dt = datetime(2024, 1, 1, 12, 0, 0)
        
        result = converter._serialize_for_json(dt)
        
        assert result == "2024-01-01T12:00:00"

    def test_serialize_for_json_nested(self):
        """Test JSON serialization of nested structures."""
        converter = MCPContentConverter()
        data = {
            "timestamp": datetime(2024, 1, 1),
            "items": [
                {"created": datetime(2024, 1, 2)},
                {"created": datetime(2024, 1, 3)}
            ]
        }
        
        result = converter._serialize_for_json(data)
        
        assert result["timestamp"] == "2024-01-01T00:00:00"
        assert result["items"][0]["created"] == "2024-01-02T00:00:00"
        assert result["items"][1]["created"] == "2024-01-03T00:00:00"


class TestPreConfiguredConverters:
    """Test cases for pre-configured converter instances."""

    def test_default_converter(self):
        """Test DEFAULT_CONVERTER configuration."""
        assert DEFAULT_CONVERTER.indent is None
        assert DEFAULT_CONVERTER.ensure_ascii is False
        assert DEFAULT_CONVERTER.sort_keys is False
        assert DEFAULT_CONVERTER.include_timestamps is False

    def test_pretty_converter(self):
        """Test PRETTY_CONVERTER configuration."""
        assert PRETTY_CONVERTER.indent == 2
        assert PRETTY_CONVERTER.sort_keys is True

    def test_markdown_converter(self):
        """Test MARKDOWN_CONVERTER configuration."""
        assert MARKDOWN_CONVERTER.indent == 2
        assert MARKDOWN_CONVERTER.include_timestamps is True

    def test_compact_converter(self):
        """Test COMPACT_CONVERTER configuration."""
        assert COMPACT_CONVERTER.ensure_ascii is True
        assert COMPACT_CONVERTER.sort_keys is False


class TestCreateConverter:
    """Test cases for create_converter factory function."""

    def test_create_converter_defaults(self):
        """Test create_converter with default parameters."""
        converter = create_converter()
        
        assert converter.indent is None
        assert converter.sort_keys is False
        assert converter.include_timestamps is False

    def test_create_converter_pretty(self):
        """Test create_converter with pretty formatting."""
        converter = create_converter(pretty=True)
        
        assert converter.indent == 2
        assert converter.sort_keys is True

    def test_create_converter_with_timestamps(self):
        """Test create_converter with timestamps enabled."""
        converter = create_converter(include_timestamps=True)
        
        assert converter.include_timestamps is True

    def test_create_converter_all_options(self):
        """Test create_converter with all options."""
        converter = create_converter(
            format_style="markdown",
            pretty=True,
            include_timestamps=True
        )
        
        assert converter.indent == 2
        assert converter.sort_keys is True
        assert converter.include_timestamps is True
