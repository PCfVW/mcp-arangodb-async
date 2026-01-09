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

                # Should call entry_main with config_file=None (stdio default)
                mock_entry.assert_called_once_with(config_file=None)
                assert result == 0

    def test_explicit_server_command(self):
        """Test explicit 'server' command."""
        with patch("sys.argv", ["mcp_arangodb_async", "server"]):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main

                mock_entry.return_value = None
                result = main()

                mock_entry.assert_called_once_with(config_file=None)
                assert result == 0

    def test_server_flag(self):
        """Test server subcommand."""
        with patch("sys.argv", ["mcp_arangodb_async", "server"]):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main

                mock_entry.return_value = None
                result = main()

                mock_entry.assert_called_once_with(config_file=None)
                assert result == 0

    def test_transport_stdio_explicit(self):
        """Test server --transport stdio flag."""
        with patch("sys.argv", ["mcp_arangodb_async", "server", "--transport", "stdio"]):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main

                mock_entry.return_value = None
                result = main()

                # Should call with config_file=None (stdio is default)
                mock_entry.assert_called_once_with(config_file=None)
                assert result == 0

    def test_transport_http_basic(self):
        """Test server --transport http flag."""
        with patch("sys.argv", ["mcp_arangodb_async", "server", "--transport", "http"]):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main
                from mcp_arangodb_async.transport_config import TransportConfig

                mock_entry.return_value = None
                result = main()

                # Should call with HTTP transport config and config_file=None
                assert mock_entry.call_count == 1
                call_args = mock_entry.call_args[0]
                call_kwargs = mock_entry.call_args[1]
                assert len(call_args) == 1
                config = call_args[0]
                assert isinstance(config, TransportConfig)
                assert config.transport == "http"
                assert config.http_host == "0.0.0.0"  # Default
                assert config.http_port == 8000  # Default
                assert call_kwargs.get("config_file") is None
                assert result == 0

    def test_transport_http_custom_host(self):
        """Test server --transport http with --host flag."""
        with patch(
            "sys.argv",
            ["mcp_arangodb_async", "server", "--transport", "http", "--host", "127.0.0.1"],
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
        """Test server --transport http with --port flag."""
        with patch(
            "sys.argv", ["mcp_arangodb_async", "server", "--transport", "http", "--port", "9000"]
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
        """Test server --transport http with --stateless flag."""
        with patch(
            "sys.argv", ["mcp_arangodb_async", "server", "--transport", "http", "--stateless"]
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
        """Test server --transport http with all options."""
        with patch(
            "sys.argv",
            [
                "mcp_arangodb_async",
                "server",
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

    def test_config_file_argument_stdio(self):
        """Test server --config-file argument with stdio transport."""
        with patch(
            "sys.argv",
            ["mcp_arangodb_async", "server", "--config-file", "/path/to/custom.yaml"],
        ):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main

                mock_entry.return_value = None
                result = main()

                # Should call with config_file kwarg
                mock_entry.assert_called_once_with(config_file="/path/to/custom.yaml")
                assert result == 0

    def test_config_file_short_alias_cfgf(self):
        """Test server --cfgf short alias for --config-file."""
        with patch(
            "sys.argv",
            ["mcp_arangodb_async", "server", "--cfgf", "/path/to/short.yaml"],
        ):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main

                mock_entry.return_value = None
                result = main()

                # Should call with config_file kwarg
                mock_entry.assert_called_once_with(config_file="/path/to/short.yaml")
                assert result == 0

    def test_config_file_with_http_transport(self):
        """Test server --config-file with --transport http."""
        with patch(
            "sys.argv",
            [
                "mcp_arangodb_async",
                "server",
                "--transport",
                "http",
                "--config-file",
                "/path/to/http-config.yaml",
            ],
        ):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main
                from mcp_arangodb_async.transport_config import TransportConfig

                mock_entry.return_value = None
                result = main()

                # Should call with HTTP transport config and config_file kwarg
                assert mock_entry.call_count == 1
                call_args = mock_entry.call_args[0]
                call_kwargs = mock_entry.call_args[1]
                assert len(call_args) == 1
                config = call_args[0]
                assert isinstance(config, TransportConfig)
                assert config.transport == "http"
                assert call_kwargs.get("config_file") == "/path/to/http-config.yaml"
                assert result == 0

    def test_server_config_path_backward_compat(self):
        """Verify --config-path backward compatibility in server command."""
        with patch(
            "sys.argv",
            ["mcp_arangodb_async", "server", "--config-path", "/path/to/config.yaml"],
        ):
            with patch("mcp_arangodb_async.entry.main") as mock_entry:
                from mcp_arangodb_async.__main__ import main

                mock_entry.return_value = None
                result = main()

                # Should call with config_file kwarg (unified dest parameter)
                mock_entry.assert_called_once_with(config_file="/path/to/config.yaml")
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

                    # Should use stdio (default behavior) with config_file=None
                    mock_entry.assert_called_once_with(config_file=None)
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
            "sys.argv", ["mcp_arangodb_async", "server", "--transport", "http", "--port", "9000"]
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

    def test_cli_config_file_overrides_env_var(self):
        """Test that CLI --config-file overrides ARANGO_DATABASES_CONFIG_FILE env var."""
        with patch(
            "sys.argv",
            ["mcp_arangodb_async", "server", "--config-file", "/cli/path.yaml"],
        ):
            with patch.dict(
                "os.environ",
                {"ARANGO_DATABASES_CONFIG_FILE": "/env/path.yaml"},
            ):
                with patch("mcp_arangodb_async.entry.main") as mock_entry:
                    from mcp_arangodb_async.__main__ import main

                    mock_entry.return_value = None
                    result = main()

                    # CLI --config-file should override env var
                    mock_entry.assert_called_once_with(config_file="/cli/path.yaml")
                    assert result == 0
