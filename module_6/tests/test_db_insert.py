"""Database helper tests for schema, inserts, and idempotency."""

import pytest

from load_data import (
    REQUIRED_COLUMNS,
    create_applicants_table,
    insert_applicant,
    load_records,
    normalize_record,
    validate_record,
)
from query_data import expected_result_keys


class FakeCursor:
    """Fake cursor that captures SQL execution."""

    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, statement, params=None):
        self.connection.executions.append((statement, params))

        if params and "url" in params:
            self.connection.rows[params["url"]] = params


class FakeConnection:
    """Fake connection for unit-level DB helper testing."""

    def __init__(self):
        self.rows = {}
        self.executions = []
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        self.commits += 1


@pytest.mark.db
def test_normalize_record_maps_required_fields():
    """Verify normalization maps Module 3 and Module 5 fields."""
    record = normalize_record(
        {
            "program_name": "Computer Science",
            "entry_url": "https://example.com/1",
            "applicant_status": "Accepted",
            "standardized_program_name": "Computer Science",
            "standardized_university": "Johns Hopkins University",
        }
    )

    assert set(record.keys()) == set(REQUIRED_COLUMNS)
    assert record["program"] == "Computer Science"
    assert record["url"] == "https://example.com/1"
    assert record["status"] == "Accepted"


@pytest.mark.db
def test_validate_record_rejects_missing_required_fields():
    """Verify missing required fields fail validation."""
    with pytest.raises(ValueError):
        validate_record({"program": None, "url": None, "status": None})


@pytest.mark.db
def test_insert_applicant_writes_required_schema():
    """Verify insert helper writes a valid applicant record."""
    connection = FakeConnection()

    insert_applicant(
        connection,
        {
            "program": "Computer Science",
            "url": "https://example.com/1",
            "status": "Accepted",
        },
    )

    assert len(connection.rows) == 1
    assert connection.commits == 1
    assert connection.rows["https://example.com/1"]["program"] == "Computer Science"


@pytest.mark.db
def test_duplicate_rows_do_not_duplicate_database():
    """Verify duplicate URL inserts are idempotent."""
    connection = FakeConnection()
    row = {
        "program": "Computer Science",
        "url": "https://example.com/1",
        "status": "Accepted",
    }

    insert_applicant(connection, row)
    insert_applicant(connection, row)

    assert len(connection.rows) == 1


@pytest.mark.db
def test_load_records_uses_connection_factory():
    """Verify load_records uses the supplied connection factory."""
    connection = FakeConnection()

    def factory():
        return connection

    loaded = load_records(
        [
            {
                "program": "Computer Science",
                "url": "https://example.com/1",
                "status": "Accepted",
            }
        ],
        connection_factory=factory,
    )

    assert loaded == 1
    assert len(connection.rows) == 1


@pytest.mark.db
def test_create_table_executes_schema_sql():
    """Verify table creation executes SQL and commits."""
    connection = FakeConnection()

    create_applicants_table(connection)

    assert connection.executions
    assert connection.commits == 1


@pytest.mark.db
def test_query_function_returns_expected_keys():
    """Verify query key helper returns expected analysis keys."""
    keys = expected_result_keys()

    assert "Q1 Fall 2026 entries" in keys
    assert "Q2 Percentage international students" in keys