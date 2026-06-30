"""Tests for database configuration and safe query helpers."""

import os
from unittest.mock import patch

import pytest

import db
from db import DatabaseConfig
from query_data import (
    build_statement,
    clamp_limit,
    execute_query,
    print_results,
    run_queries,
)


class FakeQueryCursor:
    """Fake cursor for query execution tests."""

    def __init__(self):
        self.executions = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, statement, params=None):
        self.executions.append((statement, params))

    def fetchall(self):
        return [(1,)]


class FakeQueryConnection:
    """Fake connection for query execution tests."""

    def __init__(self):
        self.cursor_object = FakeQueryCursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.cursor_object


@pytest.mark.db
def test_database_config_from_environment_success():
    """Verify DB config loads from environment variables."""
    env = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "gradcafe",
        "DB_USER": "reader",
        "DB_PASSWORD": "secret",
        "DB_SSLMODE": "require",
    }

    with patch.dict(os.environ, env, clear=True):
        config = DatabaseConfig.from_environment()

    assert config.host == "localhost"
    assert config.port == 5432
    assert config.name == "gradcafe"
    assert config.user == "reader"
    assert config.password == "secret"
    assert config.sslmode == "require"


@pytest.mark.db
def test_database_config_missing_environment_raises_error():
    """Verify missing DB variables raise a clear error."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            DatabaseConfig.from_environment()


@pytest.mark.db
def test_database_config_as_dict():
    """Verify config converts to psycopg parameters."""
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        name="gradcafe",
        user="reader",
        password="secret",
        sslmode="require",
    )

    assert config.as_dict() == {
        "host": "localhost",
        "port": 5432,
        "dbname": "gradcafe",
        "user": "reader",
        "password": "secret",
        "sslmode": "require",
    }


@pytest.mark.db
def test_get_connection_uses_psycopg_connect():
    """Verify get_connection delegates to psycopg.connect."""
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        name="gradcafe",
        user="reader",
        password="secret",
    )

    with patch.object(db.psycopg, "connect") as mocked_connect:
        db.get_connection(config=config)

    mocked_connect.assert_called_once_with(**config.as_dict())


@pytest.mark.db
def test_clamp_limit_handles_invalid_and_boundaries():
    """Verify limit validation and clamping."""
    assert clamp_limit(None) == 10
    assert clamp_limit("bad") == 10
    assert clamp_limit(-10) == 1
    assert clamp_limit(5000) == 100
    assert clamp_limit(25) == 25


@pytest.mark.db
def test_build_statement_returns_sql_object():
    """Verify SQL statement is composed safely."""
    statement = build_statement("SELECT 1 LIMIT %s;")

    assert statement is not None


@pytest.mark.db
def test_execute_query_binds_parameters_and_limit():
    """Verify query execution separates SQL and parameters."""
    cursor = FakeQueryCursor()

    rows = execute_query(
        cursor,
        "SELECT COUNT(*) FROM applicants WHERE term = %s LIMIT %s;",
        ("Fall 2026",),
        5,
    )

    assert rows == [(1,)]
    assert cursor.executions[0][1] == ("Fall 2026", 5)


@pytest.mark.db
def test_run_queries_with_fake_connection_factory():
    """Verify real query helper returns expected keys using fake connection."""
    connection = FakeQueryConnection()

    def factory():
        return connection

    results = run_queries(limit=3, connection_factory=factory)

    assert "Q1 Fall 2026 entries" in results
    assert "Q2 Percentage international students" in results
    assert all(value == [(1,)] for value in results.values())


@pytest.mark.db
def test_print_results_outputs_text(capsys):
    """Verify terminal output helper."""
    print_results({"Example": [(1,)]})

    captured = capsys.readouterr()

    assert "GradCafe SQL Analysis Results" in captured.out
    assert "Example" in captured.out
    assert "(1,)" in captured.out