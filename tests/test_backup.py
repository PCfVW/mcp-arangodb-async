from __future__ import annotations

import json
import os
import pytest
from typing import Any, Dict, Iterable, List
from tempfile import TemporaryDirectory

from mcp_arangodb_async.backup import backup_collections_to_dir, validate_output_directory


class FakeCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = docs

    def __iter__(self):
        return iter(self._docs)


class FakeCollection:
    def __init__(self, name: str, docs: List[Dict[str, Any]]):
        self._name = name
        self._docs = docs

    def all(self) -> Iterable[Dict[str, Any]]:
        return FakeCursor(self._docs)

    # For create_collection API compatibility (not used in backup)
    def properties(self):
        return {"name": self._name, "type": 2}


class FakeDB:
    def __init__(self, data: Dict[str, List[Dict[str, Any]]]):
        # data: name -> list of docs
        self._data = data

    def collections(self):
        # include a system collection to ensure filtering works
        result = [{"name": "_system", "isSystem": True}]
        for name in self._data.keys():
            result.append({"name": name, "isSystem": False})
        return result

    def collection(self, name: str):
        return FakeCollection(name, self._data.get(name, []))


def test_backup_all_non_system_collections_and_counts():
    db = FakeDB({
        "users": [{"_key": "1", "name": "a"}, {"_key": "2", "name": "b"}],
        "posts": [{"_key": "10", "title": "t"}],
    })
    with TemporaryDirectory() as tmp:
        report = backup_collections_to_dir(db, output_dir=tmp)
        assert report["output_dir"] == tmp
        written = {w["collection"]: w for w in report["written"]}
        assert set(written.keys()) == {"users", "posts"}
        assert written["users"]["count"] == 2
        assert written["posts"]["count"] == 1
        # verify files exist and contain JSON array with matching length
        for name in ("users", "posts"):
            path = written[name]["path"]
            assert os.path.exists(path)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert isinstance(data, list)
            assert len(data) == written[name]["count"]


def test_backup_with_collection_filter_and_doc_limit():
    db = FakeDB({
        "users": [{"_key": str(i)} for i in range(5)],
        "logs": [{"_key": str(i)} for i in range(3)],
    })
    with TemporaryDirectory() as tmp:
        report = backup_collections_to_dir(
            db,
            output_dir=tmp,
            collections=["users"],
            doc_limit=2,
        )
        written = report["written"]
        # only users should be written
        assert len(written) == 1
        item = written[0]
        assert item["collection"] == "users"
        assert item["count"] == 2
        # ensure only one file written
        paths = [w["path"] for w in written]
        for p in paths:
            assert os.path.exists(p)
        # ensure logs not written
        assert not os.path.exists(os.path.join(tmp, "logs.json"))


def test_backup_skips_unknown_collection_names():
    db = FakeDB({"alpha": [{"_key": "1"}]})
    with TemporaryDirectory() as tmp:
        report = backup_collections_to_dir(db, output_dir=tmp, collections=["alpha", "beta"])
        written = report["written"]
        assert len(written) == 1
        assert written[0]["collection"] == "alpha"


class TestPathValidation:
    """Test the new secure path validation functionality."""

    def test_validate_output_directory_allows_temp(self):
        """Test that temp directories are allowed."""
        import tempfile
        temp_dir = tempfile.gettempdir()
        test_path = os.path.join(temp_dir, "test_backup")

        result = validate_output_directory(test_path)
        # Should return the resolved absolute path
        assert os.path.isabs(result)
        assert "test_backup" in result

    def test_validate_output_directory_allows_cwd_subdirectory(self):
        """Test that subdirectories of current working directory are allowed."""
        test_path = "backups/test"
        result = validate_output_directory(test_path)
        assert os.path.isabs(result)
        assert result.endswith("test")

    def test_validate_output_directory_rejects_traversal(self):
        """Test that path traversal attempts are rejected."""
        with pytest.raises(ValueError, match="outside allowed directories"):
            validate_output_directory("../../../etc/passwd")

        with pytest.raises(ValueError, match="outside allowed directories"):
            validate_output_directory("backup/../../../etc/passwd")

    def test_validate_output_directory_rejects_absolute_outside_roots(self):
        """Test that absolute paths outside allowed roots are rejected."""
        if os.name == 'nt':
            # Windows - try to access C:\Windows
            with pytest.raises(ValueError, match="outside allowed directories"):
                validate_output_directory("C:\\Windows\\System32")
        else:
            # Unix - try to access /etc
            with pytest.raises(ValueError, match="outside allowed directories"):
                validate_output_directory("/etc/passwd")

    def test_validate_output_directory_handles_complex_traversal(self):
        """Test that complex path traversal attempts are properly handled."""
        # These should all be rejected as they resolve outside allowed directories
        traversal_attempts = [
            "backup/../../..",
            "backup/../../../etc",
            "./../../..",
            "backup/subdir/../../../etc",
        ]

        for attempt in traversal_attempts:
            with pytest.raises(ValueError, match="outside allowed directories"):
                validate_output_directory(attempt)

    def test_validate_output_directory_normalizes_paths(self):
        """Test that paths are properly normalized."""
        test_path = "backup/./subdir/../final"
        result = validate_output_directory(test_path)

        # Should be normalized (no ./ or ../ components)
        assert "./" not in result
        assert "../" not in result
        assert result.endswith("final")

    def test_validate_output_directory_handles_empty_paths(self):
        """Test that empty paths are handled appropriately."""
        # Empty string resolves to current directory, which should be allowed
        result = validate_output_directory("")
        assert os.path.isabs(result)

        # Whitespace-only string should also resolve to current directory
        result = validate_output_directory("   ")
        assert os.path.isabs(result)
