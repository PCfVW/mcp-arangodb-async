"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError
from mcp_arangodb_async.models import (
    QueryArgs,
    ListCollectionsArgs,
    InsertArgs,
    UpdateArgs,
    RemoveArgs,
    CreateCollectionArgs,
    BackupArgs,
    ListIndexesArgs,
    CreateIndexArgs,
    DeleteIndexArgs,
    ExplainQueryArgs,
    ValidateReferencesArgs,
    InsertWithValidationArgs,
    BulkInsertArgs,
    BulkUpdateArgs,
    # New graph management models
    BackupGraphArgs,
    RestoreGraphArgs,
    BackupNamedGraphsArgs,
    ValidateGraphIntegrityArgs,
    GraphStatisticsArgs,
)


class TestPydanticModels:
    """Test all Pydantic model validation."""

    def test_query_args_valid(self):
        """Test QueryArgs with valid data."""
        args = QueryArgs(
            query="FOR doc IN users RETURN doc",
            bind_vars={"limit": 10}
        )
        
        assert args.query == "FOR doc IN users RETURN doc"
        assert args.bind_vars == {"limit": 10}

    def test_query_args_no_bind_vars(self):
        """Test QueryArgs without bind variables."""
        args = QueryArgs(query="RETURN 1")
        
        assert args.query == "RETURN 1"
        assert args.bind_vars is None

    def test_query_args_missing_query(self):
        """Test QueryArgs with missing required query."""
        with pytest.raises(ValidationError):
            QueryArgs()

    def test_list_collections_args(self):
        """Test ListCollectionsArgs (no fields)."""
        args = ListCollectionsArgs()
        assert isinstance(args, ListCollectionsArgs)

    def test_insert_args_valid(self):
        """Test InsertArgs with valid data."""
        args = InsertArgs(
            collection="users",
            document={"name": "John", "age": 30}
        )
        
        assert args.collection == "users"
        assert args.document == {"name": "John", "age": 30}

    def test_insert_args_missing_fields(self):
        """Test InsertArgs with missing required fields."""
        with pytest.raises(ValidationError):
            InsertArgs(collection="users")  # missing document
        
        with pytest.raises(ValidationError):
            InsertArgs(document={"name": "John"})  # missing collection

    def test_update_args_valid(self):
        """Test UpdateArgs with valid data."""
        args = UpdateArgs(
            collection="users",
            key="123",
            update={"age": 31}
        )
        
        assert args.collection == "users"
        assert args.key == "123"
        assert args.update == {"age": 31}

    def test_update_args_missing_fields(self):
        """Test UpdateArgs with missing required fields."""
        with pytest.raises(ValidationError):
            UpdateArgs(collection="users", key="123")  # missing update

    def test_remove_args_valid(self):
        """Test RemoveArgs with valid data."""
        args = RemoveArgs(collection="users", key="123")
        
        assert args.collection == "users"
        assert args.key == "123"

    def test_remove_args_missing_fields(self):
        """Test RemoveArgs with missing required fields."""
        with pytest.raises(ValidationError):
            RemoveArgs(collection="users")  # missing key

    def test_create_collection_args_defaults(self):
        """Test CreateCollectionArgs with defaults."""
        args = CreateCollectionArgs(name="test_collection")
        
        assert args.name == "test_collection"
        assert args.type == "document"  # default
        assert args.waitForSync is None  # default

    def test_create_collection_args_edge(self):
        """Test CreateCollectionArgs for edge collection."""
        args = CreateCollectionArgs(
            name="edges",
            type="edge",
            waitForSync=True
        )
        
        assert args.name == "edges"
        assert args.type == "edge"
        assert args.waitForSync is True

    def test_create_collection_args_invalid_type(self):
        """Test CreateCollectionArgs with invalid type."""
        with pytest.raises(ValidationError):
            CreateCollectionArgs(name="test", type="invalid")

    def test_backup_args_defaults(self):
        """Test BackupArgs with defaults."""
        args = BackupArgs()
        
        assert args.output_dir is None
        assert args.collection is None
        assert args.collections is None
        assert args.doc_limit is None

    def test_backup_args_with_values(self):
        """Test BackupArgs with all values."""
        args = BackupArgs(
            output_dir="/tmp/backup",
            collections=["users", "products"],
            doc_limit=100
        )
        
        assert args.output_dir == "/tmp/backup"
        assert args.collections == ["users", "products"]
        assert args.doc_limit == 100

    def test_backup_args_alias_support(self):
        """Test BackupArgs with field aliases."""
        # Test using aliases
        data = {
            "outputDir": "/tmp/backup",
            "docLimit": 50
        }
        args = BackupArgs(**data)
        
        assert args.output_dir == "/tmp/backup"
        assert args.doc_limit == 50

    def test_backup_args_invalid_doc_limit(self):
        """Test BackupArgs with invalid doc_limit."""
        with pytest.raises(ValidationError):
            BackupArgs(doc_limit=0)  # must be >= 1
        
        with pytest.raises(ValidationError):
            BackupArgs(doc_limit=-5)  # must be >= 1

    def test_model_json_schema_generation(self):
        """Test that models can generate JSON schemas."""
        # This is important for MCP tool registration
        schema = QueryArgs.model_json_schema()
        
        assert "properties" in schema
        assert "query" in schema["properties"]
        assert schema["properties"]["query"]["type"] == "string"
        assert "required" in schema
        assert "query" in schema["required"]

    def test_index_models(self):
        """Test index-related model validation."""
        ListIndexesArgs(collection="users")
        ci = CreateIndexArgs(collection="users", type="persistent", fields=["email"], unique=True)
        assert ci.type == "persistent"
        DeleteIndexArgs(collection="users", id_or_name="users/123")

    def test_explain_and_validation_models(self):
        """Test explain and reference validation models."""
        ExplainQueryArgs(query="RETURN 1", max_plans=2, suggest_indexes=False)
        ValidateReferencesArgs(collection="orders", reference_fields=["user_id"], fix_invalid=False)
        InsertWithValidationArgs(collection="orders", document={"_key": "1", "user_id": "users/1"}, reference_fields=["user_id"])

    def test_bulk_models(self):
        """Test bulk insert/update model validation."""
        BulkInsertArgs(collection="users", documents=[{"_key": "1"}], batch_size=10, on_error="continue")
        BulkUpdateArgs(collection="users", updates=[{"key": "1", "update": {"age": 1}}], batch_size=10)

    def test_model_dump_exclude_none(self):
        """Test model serialization excluding None values."""
        args = BackupArgs(output_dir="/tmp/backup")
        dumped = args.model_dump(exclude_none=True)

        assert "output_dir" in dumped
        assert "collection" not in dumped  # None value excluded
        assert "collections" not in dumped  # None value excluded
        assert "doc_limit" not in dumped  # None value excluded


class TestGraphManagementModels:
    """Test cases for new graph management Pydantic models."""

    def test_backup_graph_args_valid(self):
        """Test BackupGraphArgs with valid inputs."""
        args = BackupGraphArgs(
            graph_name="social_network",
            output_dir="/tmp/graph_backup",
            include_metadata=True,
            doc_limit=1000
        )
        assert args.graph_name == "social_network"
        assert args.output_dir == "/tmp/graph_backup"
        assert args.include_metadata is True
        assert args.doc_limit == 1000

    def test_backup_graph_args_minimal(self):
        """Test BackupGraphArgs with minimal required fields."""
        args = BackupGraphArgs(graph_name="test_graph")
        assert args.graph_name == "test_graph"
        assert args.output_dir is None
        assert args.include_metadata is True  # default
        assert args.doc_limit is None

    def test_backup_graph_args_aliases(self):
        """Test BackupGraphArgs with field aliases."""
        args = BackupGraphArgs(
            graph_name="test",
            outputDir="/tmp/backup",
            includeMetadata=False,
            docLimit=500
        )
        assert args.output_dir == "/tmp/backup"
        assert args.include_metadata is False
        assert args.doc_limit == 500

    def test_backup_graph_args_validation_error(self):
        """Test BackupGraphArgs validation errors."""
        with pytest.raises(ValidationError):
            BackupGraphArgs()  # Missing required graph_name

        with pytest.raises(ValidationError):
            BackupGraphArgs(graph_name="test", doc_limit=0)  # doc_limit must be >= 1

    def test_restore_graph_args_valid(self):
        """Test RestoreGraphArgs with valid inputs."""
        args = RestoreGraphArgs(
            input_dir="/tmp/backup",
            graph_name="restored_graph",
            conflict_resolution="overwrite",
            validate_integrity=False
        )
        assert args.input_dir == "/tmp/backup"
        assert args.graph_name == "restored_graph"
        assert args.conflict_resolution == "overwrite"
        assert args.validate_integrity is False

    def test_restore_graph_args_minimal(self):
        """Test RestoreGraphArgs with minimal required fields."""
        args = RestoreGraphArgs(input_dir="/tmp/backup")
        assert args.input_dir == "/tmp/backup"
        assert args.graph_name is None
        assert args.conflict_resolution == "error"  # default
        assert args.validate_integrity is True  # default

    def test_restore_graph_args_aliases(self):
        """Test RestoreGraphArgs with field aliases."""
        args = RestoreGraphArgs(
            inputDir="/tmp/backup",
            graphName="test",
            conflictResolution="skip",
            validateIntegrity=False
        )
        assert args.input_dir == "/tmp/backup"
        assert args.graph_name == "test"
        assert args.conflict_resolution == "skip"
        assert args.validate_integrity is False

    def test_restore_graph_args_validation_error(self):
        """Test RestoreGraphArgs validation errors."""
        with pytest.raises(ValidationError):
            RestoreGraphArgs()  # Missing required input_dir

        with pytest.raises(ValidationError):
            RestoreGraphArgs(input_dir="/tmp", conflict_resolution="invalid")  # Invalid literal

    def test_backup_named_graphs_args_valid(self):
        """Test BackupNamedGraphsArgs with valid inputs."""
        args = BackupNamedGraphsArgs(
            output_file="/tmp/graphs.json",
            graph_names=["graph1", "graph2"]
        )
        assert args.output_file == "/tmp/graphs.json"
        assert args.graph_names == ["graph1", "graph2"]

    def test_backup_named_graphs_args_minimal(self):
        """Test BackupNamedGraphsArgs with minimal fields."""
        args = BackupNamedGraphsArgs()
        assert args.output_file is None
        assert args.graph_names is None

    def test_backup_named_graphs_args_aliases(self):
        """Test BackupNamedGraphsArgs with field aliases."""
        args = BackupNamedGraphsArgs(
            outputFile="/tmp/backup.json",
            graphNames=["test_graph"]
        )
        assert args.output_file == "/tmp/backup.json"
        assert args.graph_names == ["test_graph"]

    def test_validate_graph_integrity_args_valid(self):
        """Test ValidateGraphIntegrityArgs with valid inputs."""
        args = ValidateGraphIntegrityArgs(
            graph_name="test_graph",
            check_orphaned_edges=False,
            check_constraints=False,
            return_details=True
        )
        assert args.graph_name == "test_graph"
        assert args.check_orphaned_edges is False
        assert args.check_constraints is False
        assert args.return_details is True

    def test_validate_graph_integrity_args_defaults(self):
        """Test ValidateGraphIntegrityArgs with default values."""
        args = ValidateGraphIntegrityArgs()
        assert args.graph_name is None
        assert args.check_orphaned_edges is True  # default
        assert args.check_constraints is True  # default
        assert args.return_details is False  # default

    def test_validate_graph_integrity_args_aliases(self):
        """Test ValidateGraphIntegrityArgs with field aliases."""
        args = ValidateGraphIntegrityArgs(
            graphName="test",
            checkOrphanedEdges=False,
            checkConstraints=False,
            returnDetails=True
        )
        assert args.graph_name == "test"
        assert args.check_orphaned_edges is False
        assert args.check_constraints is False
        assert args.return_details is True

    def test_graph_statistics_args_valid(self):
        """Test GraphStatisticsArgs with valid inputs."""
        args = GraphStatisticsArgs(
            graph_name="analytics_graph",
            include_degree_distribution=False,
            include_connectivity=False,
            sample_size=500
        )
        assert args.graph_name == "analytics_graph"
        assert args.include_degree_distribution is False
        assert args.include_connectivity is False
        assert args.sample_size == 500

    def test_graph_statistics_args_defaults(self):
        """Test GraphStatisticsArgs with default values."""
        args = GraphStatisticsArgs()
        assert args.graph_name is None
        assert args.include_degree_distribution is True  # default
        assert args.include_connectivity is True  # default
        assert args.sample_size is None

    def test_graph_statistics_args_aliases(self):
        """Test GraphStatisticsArgs with field aliases."""
        args = GraphStatisticsArgs(
            graphName="test",
            includeDegreeDistribution=False,
            includeConnectivity=False,
            sampleSize=200
        )
        assert args.graph_name == "test"
        assert args.include_degree_distribution is False
        assert args.include_connectivity is False
        assert args.sample_size == 200

    def test_graph_statistics_args_validation_error(self):
        """Test GraphStatisticsArgs validation errors."""
        with pytest.raises(ValidationError):
            GraphStatisticsArgs(sample_size=50)  # sample_size must be >= 100
