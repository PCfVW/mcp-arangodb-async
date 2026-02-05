# V4 Test Suite for ArangoDB MCP Server

This directory contains comprehensive unit tests for all v4 tools using Test-Driven Development (TDD) methodology.

## Test Organization

### Test Files

1. **test_database_v4.py** - Database tool tests
   - 4 operations: list, get_focused, switch, get_resolution
   - Tests for multi-database support and session management

2. **test_collection_v4.py** - Collection tool tests
   - 23 operations across CRUD, Batch, Index, Schema, Management, Backup
   - MongoDB-style filter support ($gt, $gte, $lt, $lte, $ne, $in)
   - Import/export with upsert functionality

3. **test_view_v4.py** - View tool tests
   - 6 operations: create, drop, list, get, update, search
   - ArangoSearch view management
   - Full-text search capabilities

4. **test_graph_v4.py** - Graph tool tests
   - 12 operations: management, edge, traversal, backup, analysis
   - Graph creation and traversal algorithms
   - Graph integrity validation

5. **test_aql_v4.py** - AQL tool tests
   - 4 operations: query, explain, profile, build
   - Query execution and performance profiling
   - Query plan analysis and optimization suggestions

6. **test_mcp_v4.py** - MCP metadata tool tests
   - 6 operations: search_tools, list_by_category, get_workflow, list_workflows, usage_stats, unload
   - Tool discovery and categorization
   - Workflow management and usage statistics

### Shared Fixtures (conftest.py)

Provides:
- `mock_db`: Mocked ArangoDB database connection
- `mock_collection`: Mocked collection
- `mock_graph`: Mocked graph
- `mock_view`: Mocked view
- `sample_document`: Sample document for testing
- `sample_documents`: Multiple sample documents
- `sample_edge`: Sample edge document
- `data_factory`: Test data factory for creating test datasets
- `arango_config`: Test configuration

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test file
```bash
pytest tests/test_collection_v4.py
```

### Run specific test class
```bash
pytest tests/test_collection_v4.py::TestCollectionCRUD
```

### Run specific test function
```bash
pytest tests/test_collection_v4.py::TestCollectionCRUD::test_insert_single_document
```

### Run tests with coverage
```bash
pytest tests/ --cov=mcp_arangodb_async --cov-report=html
```

### Run tests by marker
```bash
pytest tests/ -m database    # Run database tests
pytest tests/ -m crud        # Run CRUD operation tests
pytest tests/ -m unit        # Run unit tests (mocked)
```

### Run with verbose output
```bash
pytest tests/ -v
```

### Run with detailed error output
```bash
pytest tests/ -vv --tb=long
```

## Test Coverage

| Tool | Operations | Tests | Status |
|------|-----------|-------|--------|
| database | 4 | 13+ | ✅ |
| collection | 23 | 35+ | ✅ |
| view | 6 | 16+ | ✅ |
| graph | 12 | 18+ | ✅ |
| aql | 4 | 20+ | ✅ |
| mcp | 6 | 20+ | ✅ |
| **Total** | **55** | **120+** | ✅ |

## Test Methodology

### TDD Approach

All tests follow Test-Driven Development practices:

1. **Test Definition** - Define what operation should do
2. **Mock Dependencies** - Mock ArangoDB connections and responses
3. **Implementation Verification** - Ensure operations work as specified
4. **Edge Case Handling** - Test error conditions and boundary cases

### Mocking Strategy

- All tests use mocked ArangoDB connections (no real database required)
- Mock objects configured with expected return values
- Side effects and exceptions tested appropriately

### Test Classes

- **TestDatabaseList**: Database listing operations
- **TestCollectionCRUD**: Create, Read, Update, Delete operations
- **TestCollectionBatch**: Bulk import/export operations
- **TestCollectionIndex**: Index management
- **TestCollectionSchema**: Schema validation
- **TestViewManagement**: View creation and management
- **TestViewSearch**: Full-text search operations
- **TestGraphTraversal**: Graph traversal algorithms
- **TestAQLExplain**: Query execution planning
- **TestAQLProfile**: Query performance profiling
- **TestMCPToolSearch**: Tool discovery
- **TestMCPWorkflows**: Workflow management

## Integration Testing

For integration tests with real ArangoDB:

1. Create `.env` file in project root (or set environment variables):
```bash
# .env
ARANGO_HOST=localhost
ARANGO_PORT=8529
ARANGO_USERNAME=root
ARANGO_PASSWORD=your_password
ARANGO_DATABASE=_system
```

2. Run integration tests:
```bash
pytest tests/ -m integration
```

Note: Unit tests are isolated and don't require ArangoDB connection.

## Architecture Alignment

Tests are organized to match v4 architecture:
- One test file per tool module
- Tests cover all operations defined in models.py
- Handler dispatch mechanisms tested
- Pydantic model validation tested

## Best Practices

1. **Independence**: Each test is independent and can run in any order
2. **Clarity**: Test names clearly describe what is being tested
3. **Isolation**: Tests use mocks to avoid external dependencies
4. **Completeness**: Edge cases and error conditions included
5. **Maintainability**: Tests follow consistent patterns and structure

## Adding New Tests

When adding new operations:

1. Add test class following existing pattern
2. Use appropriate fixtures from conftest.py
3. Test success case, error cases, and edge cases
4. Update this README with new test count
5. Run full test suite to ensure compatibility

## Dependencies

- pytest >= 6.0
- unittest.mock (standard library)
- All dependencies from main package

## References

- Architecture: [docs-v4/ARCHITECTURE_V4.md](../docs-v4/ARCHITECTURE_V4.md)
- Models: Individual `models.py` files in each tool module
- Operations: Individual operation files in tool modules
