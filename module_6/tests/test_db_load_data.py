"""Tests for database loading helpers."""

import json
from pathlib import Path

import pytest

from db import load_data


class FakeCursor:
    """Fake cursor for DB helper tests."""

    def __init__(self, connection):
        self.connection = connection
        self.rowcount = 0
        self.fetchone_value = None

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
        return self.fetchone_value

    def fetchall(self):
        """Return fake query rows."""
        return [(0,)]
        

class FakeConnection:
    """Fake connection."""

    def __init__(self):
        self.executions = []
        self.urls = set()

    def cursor(self):
        return FakeCursor(self)


@pytest.mark.db
def test_normalize_record_defaults():
    """Normalize record maps expected fields."""
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
def test_load_seed_json(tmp_path):
    """Seed JSON loader reads records."""
    path = tmp_path / "data.json"
    path.write_text(json.dumps([{"url": "x"}]), encoding="utf-8")

    records = load_data.load_seed_json(path)

    assert records == [{"url": "x"}]


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
def test_create_schema_executes_sql():
    """Schema creation executes SQL."""
    connection = FakeConnection()

    load_data.create_schema(connection)

    assert connection.executions


@pytest.mark.db
def test_query_analysis_returns_expected_keys():
    """Query analysis returns expected result keys."""
    connection = FakeConnection()

    results = load_data.query_analysis(connection)

    assert "Q1 Fall 2026 entries" in results
    assert "Q2 Percentage international students" in results
    assert "Q3 Average GPA" in results