"""Unit tests for arango_admin tool (v4).

Tests for admin operations:
- AQL forwarding: aql_query, aql_explain, aql_profile, aql_build
- Template: template_execute
- Optimize: sync_run, optimize_run, quality_check, embedding_run
"""

import sys
import pytest
from unittest.mock import MagicMock, patch, Mock

# Mock heavy ML dependencies before importing admin handler
for mod in ["numpy", "torch", "transformers"]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()
# Mock submodules that embedding engine uses
for mod in ["torch.nn", "torch.nn.functional", "transformers.AutoTokenizer", "transformers.AutoModel"]:
    sys.modules[mod] = MagicMock()

from mcp_arangodb_async.admin.handler import handle_admin
from mcp_arangodb_async.admin.models import AdminArgs


class TestAdminAQLForwarding:
    """Test admin AQL forwarding actions."""

    def test_aql_query_forwards_to_aql_handler(self, mock_db):
        """Should forward aql_query to aql handler."""
        mock_db.aql.execute.return_value = iter([{"result": 1}])
        args = {"query": "RETURN 1"}

        result = handle_admin(mock_db, "aql_query", args)

        assert isinstance(result, (list, dict))

    def test_aql_explain_forwards_to_aql_handler(self, mock_db):
        """Should forward aql_explain to aql handler."""
        mock_db.aql.explain.return_value = {"plans": [], "warnings": []}
        args = {"query": "RETURN 1"}

        result = handle_admin(mock_db, "aql_explain", args)

        assert isinstance(result, dict)
        assert "plans" in result

    def test_aql_profile_forwards_to_aql_handler(self, mock_db):
        """Should forward aql_profile to aql handler."""
        mock_db.aql.execute.return_value = iter([])
        args = {"query": "RETURN 1"}

        result = handle_admin(mock_db, "aql_profile", args)

        assert isinstance(result, dict)

    def test_aql_build_forwards_to_aql_handler(self, mock_db):
        """Should forward aql_build to aql handler."""
        mock_db.aql.execute.return_value = iter([])
        args = {"collection": "notes"}

        result = handle_admin(mock_db, "aql_build", args)

        assert isinstance(result, (list, dict))


class TestAdminTemplateForwarding:
    """Test admin template forwarding."""

    def test_template_execute_forwards_to_template_handler(self, mock_db):
        """Should forward template_execute to template handler."""
        mock_db.aql.execute.return_value = iter([])
        args = {"name": "nonexistent.template", "params": {}}

        result = handle_admin(mock_db, "template_execute", args)

        assert isinstance(result, dict)
        # Missing template returns error with available list
        assert "error" in result or "results" in result


class TestAdminOptimizeForwarding:
    """Test admin optimize forwarding actions."""

    def test_sync_run_forwards_to_optimize_handler(self, mock_db):
        """Should forward sync_run to optimize handler."""
        mock_db.has_collection.return_value = True
        mock_db.aql.execute.return_value = iter([])
        args = {"dry_run": True}

        result = handle_admin(mock_db, "sync_run", args)

        assert isinstance(result, dict)

    def test_optimize_run_forwards_to_optimize_handler(self, mock_db):
        """Should forward optimize_run to optimize handler."""
        mock_db.has_collection.return_value = True
        mock_db.aql.execute.return_value = iter([])
        args = {}

        result = handle_admin(mock_db, "optimize_run", args)

        assert isinstance(result, dict)

    def test_quality_check_forwards_to_optimize_handler(self, mock_db):
        """Should forward quality_check to optimize handler."""
        mock_db.has_collection.return_value = True
        mock_db.aql.execute.return_value = iter([])
        args = {}

        result = handle_admin(mock_db, "quality_check", args)

        assert isinstance(result, dict)

    def test_embedding_run_forwards_to_optimize_handler(self, mock_db):
        """Should forward embedding_run to optimize handler."""
        mock_db.has_collection.return_value = True
        mock_db.aql.execute.return_value = iter([])
        args = {"embedding_action": "status"}

        result = handle_admin(mock_db, "embedding_run", args)

        assert isinstance(result, dict)


class TestAdminHandlerDispatch:
    """Test admin handler dispatch mechanism."""

    def test_unknown_action_returns_error(self, mock_db):
        """Should return error with available actions for unknown action."""
        result = handle_admin(mock_db, "unknown_action", {})

        assert "error" in result
        assert "available_actions" in result

    def test_all_actions_dispatch_without_exception(self, mock_db):
        """Should dispatch all known actions without raising."""
        mock_db.aql.execute.return_value = iter([])
        mock_db.aql.explain.return_value = {"plans": [], "warnings": []}
        mock_db.has_collection.return_value = True

        actions = [
            ("aql_query", {"query": "RETURN 1"}),
            ("aql_explain", {"query": "RETURN 1"}),
            ("aql_profile", {"query": "RETURN 1"}),
            ("aql_build", {"collection": "notes"}),
            ("template_execute", {"name": "test.query", "params": {}}),
            ("sync_run", {"dry_run": True}),
            ("quality_check", {}),
            ("embedding_run", {"embedding_action": "status"}),
        ]

        for action, args in actions:
            result = handle_admin(mock_db, action, args)
            assert isinstance(result, (dict, list)), f"Action {action} returned unexpected type"


class TestAdminModels:
    """Test AdminArgs model validation."""

    def test_admin_args_aql_query(self):
        """Should validate AdminArgs with aql_query action."""
        args = AdminArgs(action="aql_query")
        assert args.action == "aql_query"

    def test_admin_args_sync_run(self):
        """Should validate AdminArgs with sync_run action."""
        args = AdminArgs(action="sync_run")
        assert args.action == "sync_run"

    def test_admin_args_embedding_run(self):
        """Should validate AdminArgs with embedding_run action."""
        args = AdminArgs(action="embedding_run")
        assert args.action == "embedding_run"

    def test_admin_args_rejects_invalid_action(self):
        """Should reject invalid action values."""
        with pytest.raises(Exception):
            AdminArgs(action="invalid_action")
