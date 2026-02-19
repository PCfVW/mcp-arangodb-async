"""Security and validation tests.

Covers AQL injection prevention, input validation, and partial-failure semantics
identified during Codex reviews:

- _validate_field_name: first-char rule, special chars, dot-nested, empty
- _validate_collection_name: hyphens, special chars, empty
- validate_references: dot-paths in ref_fields, bind var usage
- bulk_insert: ArangoServerError objects counted as error_count (not inserted_count)
- export_documents: field name injection via filter keys
- find (crud): filter field name injection
- aql/builder: collection-name hyphen, field first-char rule, nested field paths
"""

import pytest
from unittest.mock import MagicMock, patch
from arango.exceptions import ArangoServerError

from mcp_arangodb_async.collection.crud import _validate_field_name as crud_validate_field
from mcp_arangodb_async.collection.crud import find
from mcp_arangodb_async.collection.batch import _validate_field_name as batch_validate_field
from mcp_arangodb_async.collection.batch import bulk_insert, export_documents
from mcp_arangodb_async.collection.schema import (
    _validate_field_name as schema_validate_field,
    _validate_collection_name as schema_validate_collection,
    validate_references,
)
from mcp_arangodb_async.graph.traversal import _validate_collection_name as traversal_validate_collection
from mcp_arangodb_async.aql.builder import query_builder


# ---------------------------------------------------------------------------
# _validate_field_name (shared logic across crud, batch, schema)
# ---------------------------------------------------------------------------

class TestValidateFieldName:
    """Validate field name sanitization used in AQL filter clauses."""

    @pytest.mark.parametrize("validator", [
        crud_validate_field,
        batch_validate_field,
        schema_validate_field,
    ])
    def test_valid_simple_field(self, validator):
        assert validator("name") == "name"

    @pytest.mark.parametrize("validator", [
        crud_validate_field,
        batch_validate_field,
        schema_validate_field,
    ])
    def test_valid_underscore_prefix(self, validator):
        assert validator("_key") == "_key"

    @pytest.mark.parametrize("validator", [
        crud_validate_field,
        batch_validate_field,
        schema_validate_field,
    ])
    def test_valid_nested_dot_path(self, validator):
        """Dot-notation is valid for field names (but not in ref_fields)."""
        assert validator("user.email") == "user.email"

    @pytest.mark.parametrize("validator", [
        crud_validate_field,
        batch_validate_field,
        schema_validate_field,
    ])
    def test_rejects_digit_leading_field(self, validator):
        """AQL identifiers must start with letter or underscore."""
        with pytest.raises(ValueError, match="must start with"):
            validator("1field")

    @pytest.mark.parametrize("validator", [
        crud_validate_field,
        batch_validate_field,
        schema_validate_field,
    ])
    def test_rejects_hyphen_in_field(self, validator):
        with pytest.raises(ValueError):
            validator("field-name")

    @pytest.mark.parametrize("validator", [
        crud_validate_field,
        batch_validate_field,
        schema_validate_field,
    ])
    def test_rejects_semicolon_injection(self, validator):
        with pytest.raises(ValueError):
            validator("field; DROP TABLE notes")

    @pytest.mark.parametrize("validator", [
        crud_validate_field,
        batch_validate_field,
        schema_validate_field,
    ])
    def test_rejects_empty_string(self, validator):
        with pytest.raises(ValueError):
            validator("")

    @pytest.mark.parametrize("validator", [
        crud_validate_field,
        batch_validate_field,
        schema_validate_field,
    ])
    def test_rejects_none(self, validator):
        with pytest.raises((ValueError, TypeError, AttributeError)):
            validator(None)


# ---------------------------------------------------------------------------
# _validate_collection_name
# ---------------------------------------------------------------------------

class TestValidateCollectionName:
    """Validate collection name sanitization to prevent AQL injection."""

    @pytest.mark.parametrize("validator", [
        schema_validate_collection,
        traversal_validate_collection,
    ])
    def test_valid_collection_name(self, validator):
        assert validator("notes") == "notes"

    @pytest.mark.parametrize("validator", [
        schema_validate_collection,
        traversal_validate_collection,
    ])
    def test_valid_with_underscore(self, validator):
        assert validator("my_notes") == "my_notes"

    @pytest.mark.parametrize("validator", [
        schema_validate_collection,
        traversal_validate_collection,
    ])
    def test_rejects_hyphen(self, validator):
        """Hyphens cause AQL parse errors (interpreted as subtraction)."""
        with pytest.raises(ValueError, match="only \\[A-Za-z0-9_\\] allowed|Invalid collection name"):
            validator("my-notes")

    @pytest.mark.parametrize("validator", [
        schema_validate_collection,
        traversal_validate_collection,
    ])
    def test_rejects_space(self, validator):
        with pytest.raises(ValueError):
            validator("my notes")

    @pytest.mark.parametrize("validator", [
        schema_validate_collection,
        traversal_validate_collection,
    ])
    def test_rejects_semicolon_injection(self, validator):
        with pytest.raises(ValueError):
            validator("notes; FOR x IN secrets RETURN x")

    @pytest.mark.parametrize("validator", [
        schema_validate_collection,
        traversal_validate_collection,
    ])
    def test_rejects_empty(self, validator):
        with pytest.raises(ValueError):
            validator("")


# ---------------------------------------------------------------------------
# validate_references: dot-paths rejected, bind vars used
# ---------------------------------------------------------------------------

class TestValidateReferences:
    """validate_references must reject dot-paths and use bind vars."""

    def _make_db(self, collection_docs=None):
        db = MagicMock()
        col = MagicMock()
        col.count.return_value = 0
        db.collection.return_value = col
        cursor = MagicMock()
        cursor.__iter__ = MagicMock(return_value=iter(collection_docs or []))
        cursor.close = MagicMock()
        db.aql.execute.return_value = cursor
        return db

    def test_rejects_dot_in_ref_field(self):
        """Dot-notation in reference_fields silently fails in AQL; must be rejected."""
        db = self._make_db()
        with pytest.raises(ValueError, match="contains a dot"):
            validate_references(
                db,
                {"collection": "notes", "reference_fields": ["user.id"]},
            )

    def test_rejects_hyphen_in_ref_field(self):
        with pytest.raises(ValueError):
            validate_references(
                db := self._make_db(),
                {"collection": "notes", "reference_fields": ["field-name"]},
            )

    def test_uses_bind_vars_for_ref_fields(self):
        """ref_fields must be passed as bind variable, not interpolated into AQL."""
        db = self._make_db()
        validate_references(
            db,
            {"collection": "notes", "reference_fields": ["author_id"]},
        )
        call_kwargs = db.aql.execute.call_args
        bind_vars = call_kwargs[1].get("bind_vars") or call_kwargs[0][1]
        assert "ref_fields" in bind_vars
        assert bind_vars["ref_fields"] == ["author_id"]

    def test_accepts_valid_top_level_field(self):
        """Valid top-level field names should not raise."""
        db = self._make_db()
        result = validate_references(
            db,
            {"collection": "notes", "reference_fields": ["author_id", "parent_id"]},
        )
        assert "validation_passed" in result


# ---------------------------------------------------------------------------
# bulk_insert: partial failure counting
# ---------------------------------------------------------------------------

class TestBulkInsertPartialFailure:
    """insert_many returns ArangoServerError objects for individual doc failures.

    These must be counted as error_count, not inserted_count.
    """

    def _make_arango_error(self):
        """Construct a minimal ArangoServerError-like object."""
        err = MagicMock(spec=ArangoServerError)
        # Ensure isinstance(err, dict) is False
        return err

    def test_all_success(self, mock_db):
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col
        mock_db.has_collection.return_value = True
        mock_col.insert_many.return_value = [
            {"_key": "a", "_id": "col/a"},
            {"_key": "b", "_id": "col/b"},
        ]
        result = bulk_insert(mock_db, {"collection": "col", "documents": [{"x": 1}, {"x": 2}]})
        assert result["inserted_count"] == 2
        assert result["error_count"] == 0

    def test_partial_failure_counts_errors(self, mock_db):
        """One success + one ArangoServerError → inserted_count=1, error_count=1."""
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col
        mock_db.has_collection.return_value = True
        err = self._make_arango_error()
        mock_col.insert_many.return_value = [
            {"_key": "ok", "_id": "col/ok"},
            err,
        ]
        result = bulk_insert(mock_db, {"collection": "col", "documents": [{"x": 1}, {"x": 2}]})
        assert result["inserted_count"] == 1
        assert result["error_count"] == 1

    def test_all_failure_counts_correctly(self, mock_db):
        """All ArangoServerError → inserted_count=0, error_count=2."""
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col
        mock_db.has_collection.return_value = True
        mock_col.insert_many.return_value = [
            self._make_arango_error(),
            self._make_arango_error(),
        ]
        result = bulk_insert(mock_db, {"collection": "col", "documents": [{"x": 1}, {"x": 2}]})
        assert result["inserted_count"] == 0
        assert result["error_count"] == 2

    def test_success_rate_reflects_partial(self, mock_db):
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col
        mock_db.has_collection.return_value = True
        mock_col.insert_many.return_value = [
            {"_key": "ok", "_id": "col/ok"},
            self._make_arango_error(),
            self._make_arango_error(),
            self._make_arango_error(),
        ]
        result = bulk_insert(mock_db, {
            "collection": "col",
            "documents": [{"x": 1}, {"x": 2}, {"x": 3}, {"x": 4}],
        })
        assert abs(result["success_rate"] - 0.25) < 1e-9


# ---------------------------------------------------------------------------
# find (crud.py): filter field injection
# ---------------------------------------------------------------------------

class TestFindFilterInjection:
    """find() must reject invalid field names in filter dict keys."""

    def test_valid_filter_executes(self, mock_db):
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col
        mock_db.has_collection.return_value = True
        cursor = MagicMock()
        cursor.__iter__ = MagicMock(return_value=iter([{"_key": "1"}]))
        mock_db.aql.execute.return_value = cursor
        result = find(mock_db, {"collection": "notes", "filter": {"weight": {"$gt": 10}}})
        assert result["count"] == 1

    def test_hyphen_in_filter_key_rejected(self, mock_db):
        mock_db.has_collection.return_value = True
        with pytest.raises(ValueError):
            find(mock_db, {"collection": "notes", "filter": {"field-name": "value"}})

    def test_digit_leading_filter_key_rejected(self, mock_db):
        mock_db.has_collection.return_value = True
        with pytest.raises(ValueError, match="must start with"):
            find(mock_db, {"collection": "notes", "filter": {"1field": "value"}})

    def test_injection_attempt_in_filter_key_rejected(self, mock_db):
        mock_db.has_collection.return_value = True
        with pytest.raises(ValueError):
            find(mock_db, {
                "collection": "notes",
                "filter": {"x == null RETURN doc //": "ignored"},
            })


# ---------------------------------------------------------------------------
# export_documents (batch.py): filter field injection
# ---------------------------------------------------------------------------

class TestExportFilterInjection:
    """export_documents must validate filter keys used in AQL conditions."""

    def test_hyphen_in_filter_key_rejected(self, mock_db):
        mock_db.has_collection.return_value = True
        result = export_documents(mock_db, {
            "collection": "notes",
            "filter": {"field-name": "value"},
        })
        assert "error" in result

    def test_digit_leading_filter_key_rejected(self, mock_db):
        mock_db.has_collection.return_value = True
        result = export_documents(mock_db, {
            "collection": "notes",
            "filter": {"1bad": "value"},
        })
        assert "error" in result

    def test_valid_filter_key_accepted(self, mock_db, tmp_path):
        mock_db.has_collection.return_value = True
        cursor = MagicMock()
        cursor.__iter__ = MagicMock(return_value=iter([{"_key": "1", "weight": 50}]))
        mock_db.aql.execute.return_value = cursor
        result = export_documents(mock_db, {
            "collection": "notes",
            "filter": {"weight": {"$gte": 30}},
            "options": {"output_dir": str(tmp_path)},
        })
        assert result.get("success") is True
        assert result["count"] == 1


# ---------------------------------------------------------------------------
# aql/builder.py: collection name and field name validation
# ---------------------------------------------------------------------------

class TestQueryBuilderValidation:
    """query_builder must reject invalid collection names and field names."""

    def test_hyphen_in_collection_rejected(self, mock_db):
        with pytest.raises(ValueError, match="Invalid collection name"):
            query_builder(mock_db, {"collection": "my-notes"})

    def test_space_in_collection_rejected(self, mock_db):
        with pytest.raises(ValueError, match="Invalid collection name"):
            query_builder(mock_db, {"collection": "my notes"})

    def test_valid_collection_executes(self, mock_db):
        cursor = MagicMock()
        cursor.__iter__ = MagicMock(return_value=iter([]))
        cursor.close = MagicMock()
        mock_db.aql.execute.return_value = cursor
        result = query_builder(mock_db, {"collection": "notes"})
        assert isinstance(result, list)

    def test_digit_leading_filter_field_rejected(self, mock_db):
        with pytest.raises(ValueError, match="must start with"):
            query_builder(mock_db, {
                "collection": "notes",
                "filters": [{"field": "1bad", "op": "==", "value": 1}],
            })

    def test_hyphen_in_filter_field_rejected(self, mock_db):
        with pytest.raises(ValueError):
            query_builder(mock_db, {
                "collection": "notes",
                "filters": [{"field": "field-name", "op": "==", "value": "x"}],
            })

    def test_unsupported_operator_rejected(self, mock_db):
        with pytest.raises(ValueError, match="Unsupported operator"):
            query_builder(mock_db, {
                "collection": "notes",
                "filters": [{"field": "name", "op": "EXEC", "value": "x"}],
            })

    def test_valid_nested_field_accepted(self, mock_db):
        cursor = MagicMock()
        cursor.__iter__ = MagicMock(return_value=iter([]))
        cursor.close = MagicMock()
        mock_db.aql.execute.return_value = cursor
        result = query_builder(mock_db, {
            "collection": "notes",
            "filters": [{"field": "meta.weight", "op": ">", "value": 10}],
        })
        assert isinstance(result, list)

    def test_invalid_sort_direction_defaults_to_asc(self, mock_db):
        cursor = MagicMock()
        cursor.__iter__ = MagicMock(return_value=iter([]))
        cursor.close = MagicMock()
        mock_db.aql.execute.return_value = cursor
        result = query_builder(mock_db, {
            "collection": "notes",
            "sort": [{"field": "weight", "direction": "INJECTED"}],
        })
        # Should not raise; direction defaults to ASC
        assert isinstance(result, list)
        aql_call = mock_db.aql.execute.call_args[0][0]
        assert "INJECTED" not in aql_call
        assert "ASC" in aql_call
