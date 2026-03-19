---
name: Test Architect
description: Guidelines for testing strategy, structure, coverage, and quality. Language-agnostic with Python specifics. Invoked only by explicit demand.
---

# Test Architect Guidelines

This skill is invoked ONLY by explicit demand and not automatically.

## 1. General Testing Strategy

- **Test Pyramid**: Prioritize unit tests (fast, isolated), then integration tests (real dependencies), then end-to-end tests (full system).
- **Quality over quantity**: Focus on testing critical paths, edge cases, and business rules. Don't write tests just for coverage numbers.
- **Coverage target**: Aim for 90%+ on business logic. Infrastructure/wiring code can have lower coverage.

## 2. Test Organization

### Python (pytest)

```
tests/
├── conftest.py              # Shared fixtures, factory functions
├── unit/
│   ├── test_discovery.py    # Unit tests for discovery module
│   └── test_dedup.py        # Unit tests for dedup module
├── integration/
│   ├── test_pipeline.py     # Tests with real file I/O
│   └── conftest.py          # Integration-specific fixtures
└── fixtures/
    ├── sample.eml
    └── sample.mbox
```

### Generic Rules

- **Test file per module**: Each source module has a corresponding test file.
- **Location**: Tests in a separate `tests/` directory (Python convention) or co-located next to source files (JS/TS convention). Follow the language's standard practice.
- **Naming**: Test files prefixed with `test_` (Python) or suffixed with `.spec.ts`/`.test.ts` (JS/TS).

## 3. Test Design Principles

- **Arrange-Act-Assert (AAA)**: Structure every test in three clear sections.
- **One assertion per concept**: Each test should verify one behavior. Multiple asserts are fine if they validate the same concept.
- **Descriptive test names**: `test_dedup_skips_already_processed_email` not `test_dedup_1`.
- **No test interdependence**: Tests must not depend on execution order or shared mutable state.
- **Test behavior, not implementation**: Test what the code does, not how it does it. Avoid asserting on internal method calls.

## 4. Fixtures & Test Data

- **Use fixtures for setup**: Use `conftest.py` (pytest) or `beforeEach` (JS) for shared setup.
- **Factory functions over raw data**: Create helper functions that build test objects with sensible defaults.
- **Real test data**: For file-processing projects, include real sample files in `tests/fixtures/`.
- **Temporary directories**: Use `tmp_path` (pytest) or `os.tmpdir()` for tests that write to disk.

## 5. Mocking Guidelines

- **Mock at boundaries**: Mock external services, APIs, file systems — not your own internal code.
- **Prefer fakes over mocks**: When possible, use fake implementations of interfaces (see Repository Pattern skill) instead of mock libraries.
- **Don't mock what you own**: If you control the code, test it directly. Only mock what you can't control.

## 6. Python-Specific (pytest)

- **Framework**: Use `pytest` (never `unittest` style classes unless the project already uses them).
- **Fixtures**: Use `@pytest.fixture` for setup/teardown. Prefer function-scoped fixtures for isolation.
- **Parametrize**: Use `@pytest.mark.parametrize` for testing multiple inputs against the same logic.
- **Markers**: Use markers (`@pytest.mark.slow`, `@pytest.mark.integration`) to categorize tests.
- **Assertions**: Use plain `assert` statements with descriptive messages. No need for `self.assertEqual`.

```python
# Example: Clean pytest test
@pytest.fixture
def storage(tmp_path):
    return FileStorageProvider(base_dir=tmp_path)

@pytest.fixture
def ingestion_service(storage):
    return IngestionService(storage=storage)

def test_ingest_email_stores_and_returns_id(ingestion_service, sample_email):
    result = ingestion_service.ingest_email(sample_email)
    assert result == sample_email.unique_id

def test_ingest_duplicate_email_is_idempotent(ingestion_service, sample_email):
    first = ingestion_service.ingest_email(sample_email)
    second = ingestion_service.ingest_email(sample_email)
    assert first == second
```
