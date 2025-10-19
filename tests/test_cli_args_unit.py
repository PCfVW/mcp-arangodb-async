"""Unit tests for CLI argument parsing (Phase 2)."""

import pytest
import sys
from unittest.mock import patch, Mock
from io import StringIO


class TestCLIArgumentParsing:
    """Test command-line argument parsing for transport configuration."""

    def test_default_no_args_runs_stdio_server(self):
        """Test that no arguments defaults to stdio server."""
        with patch("sys.argv", ["mcp_arangodb_async"]):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main

                # Mock entry_main to prevent actual server start
                mock_entry.return_value = None

                result = main()

                # Should call entry_main with no transport config (stdio default)
                mock_entry.assert_called_once_with()
                assert result == 0

    def test_explicit_server_command(self):
        """Test explicit 'server' command."""
        with patch("sys.argv", ["mcp_arangodb_async", "server"]):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main

                mock_entry.return_value = None
                result = main()

                mock_entry.assert_called_once_with()
                assert result == 0

    def test_server_flag(self):
        """Test --server flag."""
        with patch("sys.argv", ["mcp_arangodb_async", "--server"]):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main

                mock_entry.return_value = None
                result = main()

                mock_entry.assert_called_once_with()
                assert result == 0

    def test_transport_stdio_explicit(self):
        """Test --transport stdio flag."""
        with patch("sys.argv", ["mcp_arangodb_async", "--transport", "stdio"]):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main

                mock_entry.return_value = None
                result = main()

                # Should call with no config (stdio is default)
                mock_entry.assert_called_once_with()
                assert result == 0

    def test_transport_http_basic(self):
        """Test --transport http flag."""
        with patch("sys.argv", ["mcp_arangodb_async", "--transport", "http"]):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main
                from mcp_arangodb_async.transport_config import TransportConfig

                mock_entry.return_value = None
                result = main()

                # Should call with HTTP transport config
                assert mock_entry.call_count == 1
                call_args = mock_entry.call_args[0]
                assert len(call_args) == 1
                config = call_args[0]
                assert isinstance(config, TransportConfig)
                assert config.transport == "http"
                assert config.http_host == "0.0.0.0"  # Default
                assert config.http_port == 8000  # Default
                assert result == 0

    def test_transport_http_custom_host(self):
        """Test --transport http with --host flag."""
        with patch(
            "sys.argv",
            ["mcp_arangodb_async", "--transport", "http", "--host", "127.0.0.1"],
        ):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main
                from mcp_arangodb_async.transport_config import TransportConfig

                mock_entry.return_value = None
                result = main()

                call_args = mock_entry.call_args[0]
                config = call_args[0]
                assert isinstance(config, TransportConfig)
                assert config.transport == "http"
                assert config.http_host == "127.0.0.1"
                assert result == 0

    def test_transport_http_custom_port(self):
        """Test --transport http with --port flag."""
        with patch(
            "sys.argv", ["mcp_arangodb_async", "--transport", "http", "--port", "9000"]
        ):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main
                from mcp_arangodb_async.transport_config import TransportConfig

                mock_entry.return_value = None
                result = main()

                call_args = mock_entry.call_args[0]
                config = call_args[0]
                assert isinstance(config, TransportConfig)
                assert config.transport == "http"
                assert config.http_port == 9000
                assert result == 0

    def test_transport_http_stateless(self):
        """Test --transport http with --stateless flag."""
        with patch(
            "sys.argv", ["mcp_arangodb_async", "--transport", "http", "--stateless"]
        ):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main
                from mcp_arangodb_async.transport_config import TransportConfig

                mock_entry.return_value = None
                result = main()

                call_args = mock_entry.call_args[0]
                config = call_args[0]
                assert isinstance(config, TransportConfig)
                assert config.transport == "http"
                assert config.http_stateless is True
                assert result == 0

    def test_transport_http_all_options(self):
        """Test --transport http with all options."""
        with patch(
            "sys.argv",
            [
                "mcp_arangodb_async",
                "--transport",
                "http",
                "--host",
                "0.0.0.0",
                "--port",
                "8080",
                "--stateless",
            ],
        ):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main
                from mcp_arangodb_async.transport_config import TransportConfig

                mock_entry.return_value = None
                result = main()

                call_args = mock_entry.call_args[0]
                config = call_args[0]
                assert isinstance(config, TransportConfig)
                assert config.transport == "http"
                assert config.http_host == "0.0.0.0"
                assert config.http_port == 8080
                assert config.http_stateless is True
                assert result == 0


class TestCLIEnvironmentVariables:
    """Test environment variable support for transport configuration."""

    def test_env_var_transport_stdio(self):
        """Test MCP_TRANSPORT=stdio environment variable."""
        with patch("sys.argv", ["mcp_arangodb_async"]):
            with patch.dict("os.environ", {"MCP_TRANSPORT": "stdio"}):
                with patch("mcp_arangodb_async.entry.main") as mock_entry:
                    from mcp_arangodb_async.__main__ import main

                    mock_entry.return_value = None
                    result = main()

                    # Should use stdio (default behavior)
                    mock_entry.assert_called_once_with()
                    assert result == 0

    def test_env_var_transport_http(self):
        """Test MCP_TRANSPORT=http environment variable."""
        with patch("sys.argv", ["mcp_arangodb_async"]):
            with patch.dict("os.environ", {"MCP_TRANSPORT": "http"}):
                with patch("mcp_arangodb_async.entry.main") as mock_entry:
                    from mcp_arangodb_async.__main__ import main
                    from mcp_arangodb_async.transport_config import TransportConfig

                    mock_entry.return_value = None
                    result = main()

                    call_args = mock_entry.call_args[0]
                    config = call_args[0]
                    assert isinstance(config, TransportConfig)
                    assert config.transport == "http"
                    assert result == 0

    def test_env_var_http_host(self):
        """Test MCP_HTTP_HOST environment variable."""
        with patch("sys.argv", ["mcp_arangodb_async"]):
            with patch.dict(
                "os.environ", {"MCP_TRANSPORT": "http", "MCP_HTTP_HOST": "127.0.0.1"}
            ):
                with patch("mcp_arangodb_async.entry.main") as mock_entry:
                    from mcp_arangodb_async.__main__ import main
                    from mcp_arangodb_async.transport_config import TransportConfig

                    mock_entry.return_value = None
                    result = main()

                    call_args = mock_entry.call_args[0]
                    config = call_args[0]
                    assert config.http_host == "127.0.0.1"
                    assert result == 0

    def test_env_var_http_port(self):
        """Test MCP_HTTP_PORT environment variable."""
        with patch("sys.argv", ["mcp_arangodb_async"]):
            with patch.dict(
                "os.environ", {"MCP_TRANSPORT": "http", "MCP_HTTP_PORT": "9000"}
            ):
                with patch("mcp_arangodb_async.entry.main") as mock_entry:
                    from mcp_arangodb_async.__main__ import main
                    from mcp_arangodb_async.transport_config import TransportConfig

                    mock_entry.return_value = None
                    result = main()

                    call_args = mock_entry.call_args[0]
                    config = call_args[0]
                    assert config.http_port == 9000
                    assert result == 0

    def test_env_var_http_stateless_true(self):
        """Test MCP_HTTP_STATELESS=true environment variable."""
        with patch("sys.argv", ["mcp_arangodb_async"]):
            with patch.dict(
                "os.environ", {"MCP_TRANSPORT": "http", "MCP_HTTP_STATELESS": "true"}
            ):
                with patch("mcp_arangodb_async.entry.main") as mock_entry:
                    from mcp_arangodb_async.__main__ import main
                    from mcp_arangodb_async.transport_config import TransportConfig

                    mock_entry.return_value = None
                    result = main()

                    call_args = mock_entry.call_args[0]
                    config = call_args[0]
                    assert config.http_stateless is True
                    assert result == 0

    def test_env_var_http_stateless_false(self):
        """Test MCP_HTTP_STATELESS=false environment variable."""
        with patch("sys.argv", ["mcp_arangodb_async"]):
            with patch.dict(
                "os.environ", {"MCP_TRANSPORT": "http", "MCP_HTTP_STATELESS": "false"}
            ):
                with patch("mcp_arangodb_async.entry.main") as mock_entry:
                    from mcp_arangodb_async.__main__ import main
                    from mcp_arangodb_async.transport_config import TransportConfig

                    mock_entry.return_value = None
                    result = main()

                    call_args = mock_entry.call_args[0]
                    config = call_args[0]
                    assert config.http_stateless is False
                    assert result == 0

    def test_env_var_cors_origins_single(self):
        """Test MCP_HTTP_CORS_ORIGINS with single origin."""
        with patch("sys.argv", ["mcp_arangodb_async"]):
            with patch.dict(
                "os.environ",
                {
                    "MCP_TRANSPORT": "http",
                    "MCP_HTTP_CORS_ORIGINS": "https://app.example.com",
                },
            ):
                with patch("mcp_arangodb_async.entry.main") as mock_entry:
                    from mcp_arangodb_async.__main__ import main
                    from mcp_arangodb_async.transport_config import TransportConfig

                    mock_entry.return_value = None
                    result = main()

                    call_args = mock_entry.call_args[0]
                    config = call_args[0]
                    assert config.http_cors_origins == ["https://app.example.com"]
                    assert result == 0

    def test_env_var_cors_origins_multiple(self):
        """Test MCP_HTTP_CORS_ORIGINS with multiple origins."""
        with patch("sys.argv", ["mcp_arangodb_async"]):
            with patch.dict(
                "os.environ",
                {
                    "MCP_TRANSPORT": "http",
                    "MCP_HTTP_CORS_ORIGINS": "https://app.example.com,https://admin.example.com",
                },
            ):
                with patch("mcp_arangodb_async.entry.main") as mock_entry:
                    from mcp_arangodb_async.__main__ import main
                    from mcp_arangodb_async.transport_config import TransportConfig

                    mock_entry.return_value = None
                    result = main()

                    call_args = mock_entry.call_args[0]
                    config = call_args[0]
                    assert config.http_cors_origins == [
                        "https://app.example.com",
                        "https://admin.example.com",
                    ]
                    assert result == 0

    def test_cli_args_override_env_vars(self):
        """Test that CLI arguments override environment variables."""
        with patch(
            "sys.argv", ["mcp_arangodb_async", "--transport", "http", "--port", "9000"]
        ):
            with patch.dict(
                "os.environ",
                {
                    "MCP_TRANSPORT": "stdio",  # Should be overridden
                    "MCP_HTTP_PORT": "8000",  # Should be overridden
                },
            ):
                with patch("mcp_arangodb_async.entry.main") as mock_entry:
                    from mcp_arangodb_async.__main__ import main
                    from mcp_arangodb_async.transport_config import TransportConfig

                    mock_entry.return_value = None
                    result = main()

                    call_args = mock_entry.call_args[0]
                    config = call_args[0]
                    assert config.transport == "http"  # CLI wins
                    assert config.http_port == 9000  # CLI wins
                    assert result == 0
