"""Tests for Module 6 database loading helpers."""

import json

import pytest

from db import load_data


class FakeCursor:
    """Small database cursor fake used by unit tests."""

    def __init__(self, connection):
        self.connection = connection
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, statement, params=None):
        self.connection.executions.append((statement, params))

        if params and isinstance(params, dict) and params.get("url"):
            if params["url"] not in self.connection.urls:
                self.connection.urls.add(params["url"])
                self.rowcount = 1
            else:
                self.rowcount = 0

    def fetchone(self):
        if self.connection.fetchone_values:
            return self.connection.fetchone_values.pop(0)
        return None

    def fetchall(self):
        if self.connection.fetchall_values:
            return self.connection.fetchall_values.pop(0)
        return [(0,)]


class FakeConnection:
    """Small database connection fake."""

    def __init__(self):
        self.executions = []
        self.urls = set()
        self.fetchone_values = []
        self.fetchall_values = []

    def cursor(self):
        return FakeCursor(self)


@pytest.mark.db
def test_normalize_record_defaults():
    """Missing program and status receive safe defaults."""
    record = load_data.normalize_record(
        {
            "url": "https://example.com/1",
            "status": "Accepted",
        }
    )

    assert record["program"] == "Unknown"
    assert record["url"] == "https://example.com/1"
    assert record["status"] == "Accepted"


@pytest.mark.db
def test_normalize_record_all_fields():
    """All supported applicant fields are preserved."""
    source = {
        "program": "Computer Science",
        "comments": "Test",
        "date_added": "2026-01-01",
        "url": "https://example.com/2",
        "status": "Accepted",
        "term": "Fall 2026",
        "us_or_international": "International",
        "gpa": 3.9,
        "gre": 330,
        "gre_v": 165,
        "gre_aw": 5.0,
        "degree": "PhD",
        "llm_generated_program": "Computer Science",
        "llm_generated_university": "Johns Hopkins University",
    }

    assert load_data.normalize_record(source) == source


@pytest.mark.db
def test_load_seed_json(tmp_path):
    """Seed JSON loader reads records."""
    path = tmp_path / "data.json"
    path.write_text(
        json.dumps([{"url": "https://example.com/1"}]),
        encoding="utf-8",
    )

    records = load_data.load_seed_json(path)

    assert records == [{"url": "https://example.com/1"}]


@pytest.mark.db
def test_create_schema_executes_sql():
    """Schema creation executes the schema statement."""
    connection = FakeConnection()

    load_data.create_schema(connection)

    assert connection.executions
    assert "CREATE TABLE IF NOT EXISTS applicants" in connection.executions[0][0]


@pytest.mark.db
def test_get_watermark_existing():
    """Existing watermark value is returned."""
    connection = FakeConnection()
    connection.fetchone_values = [("https://example.com/10",)]

    result = load_data.get_watermark(connection, "gradcafe_seed")

    assert result == "https://example.com/10"


@pytest.mark.db
def test_get_watermark_missing():
    """Missing watermark returns None."""
    connection = FakeConnection()
    connection.fetchone_values = [None]

    result = load_data.get_watermark(connection, "gradcafe_seed")

    assert result is None


@pytest.mark.db
def test_update_watermark_executes_statement():
    """Watermark update executes an upsert."""
    connection = FakeConnection()

    load_data.update_watermark(
        connection,
        "gradcafe_seed",
        "https://example.com/20",
    )

    statement, params = connection.executions[-1]

    assert "INSERT INTO ingestion_watermarks" in statement
    assert params == ("gradcafe_seed", "https://example.com/20")


@pytest.mark.db
def test_insert_records_is_idempotent():
    """Duplicate URLs do not insert twice."""
    connection = FakeConnection()

    records = [
        {"url": "https://example.com/1", "status": "Accepted"},
        {"url": "https://example.com/1", "status": "Accepted"},
    ]

    inserted = load_data.insert_records(connection, records)

    assert inserted == 1
    assert len(connection.urls) == 1


@pytest.mark.db
def test_insert_records_skips_missing_url():
    """Records without URLs are ignored."""
    connection = FakeConnection()

    inserted = load_data.insert_records(
        connection,
        [
            {"status": "Accepted"},
            {"url": "https://example.com/1", "status": "Accepted"},
        ],
    )

    assert inserted == 1


@pytest.mark.db
def test_handle_scrape_new_data_without_watermark(tmp_path):
    """Initial ingestion processes every valid seed record."""
    path = tmp_path / "data.json"
    path.write_text(
        json.dumps(
            [
                {
                    "url": "https://example.com/1",
                    "status": "Accepted",
                },
                {
                    "url": "https://example.com/2",
                    "status": "Rejected",
                },
            ]
        ),
        encoding="utf-8",
    )

    connection = FakeConnection()
    connection.fetchone_values = [None]

    result = load_data.handle_scrape_new_data(
        connection,
        path,
        source="test_source",
    )

    assert result["processed"] == 2
    assert result["inserted"] == 2

    watermark_calls = [
        params
        for statement, params in connection.executions
        if "INSERT INTO ingestion_watermarks" in statement
    ]

    assert watermark_calls
    assert watermark_calls[-1] == (
        "test_source",
        "https://example.com/2",
    )


@pytest.mark.db
def test_handle_scrape_new_data_with_watermark(tmp_path):
    """Only records newer than the current watermark are processed."""
    path = tmp_path / "data.json"
    path.write_text(
        json.dumps(
            [
                {
                    "url": "https://example.com/1",
                    "status": "Accepted",
                },
                {
                    "url": "https://example.com/2",
                    "status": "Accepted",
                },
                {
                    "url": "https://example.com/3",
                    "status": "Accepted",
                },
            ]
        ),
        encoding="utf-8",
    )

    connection = FakeConnection()
    connection.fetchone_values = [("https://example.com/2",)]

    result = load_data.handle_scrape_new_data(
        connection,
        path,
        source="test_source",
    )

    assert result["processed"] == 1
    assert result["inserted"] == 1
    assert "https://example.com/3" in connection.urls


@pytest.mark.db
def test_recompute_analytics():
    """Analytics recomputation returns applicant count."""
    connection = FakeConnection()
    connection.fetchone_values = [(42,)]

    result = load_data.recompute_analytics(connection)

    assert result == {"applicant_count": 42}


@pytest.mark.db
def test_query_analysis_returns_expected_keys():
    """Query analysis returns all UI analysis questions."""
    connection = FakeConnection()
    connection.fetchall_values = [
        [(100,)],
        [(47.02,)],
        [(3.75,)],
    ]

    results = load_data.query_analysis(connection)

    assert results["Q1 Fall 2026 entries"] == [(100,)]
    assert results["Q2 Percentage international students"] == [(47.02,)]
    assert results["Q3 Average GPA"] == [(3.75,)]