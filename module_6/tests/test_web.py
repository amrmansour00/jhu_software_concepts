"""Tests for Module 6 Flask web service."""

import pytest

import run


class FakeConnection:
    """Fake DB connection context manager."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False


@pytest.mark.web
def test_analysis_page_loads(monkeypatch):
    """Analysis page renders results."""
    monkeypatch.setattr(run, "get_connection", lambda: FakeConnection())
    monkeypatch.setattr(
        run,
        "run_queries",
        lambda _connection: {"Q1 Fall 2026 entries": [(2,)]},
    )

    client = run.app.test_client()
    response = client.get("/analysis")

    assert response.status_code == 200
    assert b"Answer: 2" in response.data


@pytest.mark.buttons
def test_pull_data_queues_message(monkeypatch):
    """Pull Data queues scrape task."""
    calls = []

    def fake_publish(kind, payload=None):
        calls.append((kind, payload))

    monkeypatch.setattr(run, "publish_task", fake_publish)

    response = run.app.test_client().post("/pull-data")

    assert response.status_code == 202
    assert response.json["status"] == "queued"
    assert response.json["task"] == "scrape_new_data"
    assert calls[0][0] == "scrape_new_data"


@pytest.mark.buttons
def test_update_analysis_queues_message(monkeypatch):
    """Update Analysis queues recompute task."""
    calls = []

    def fake_publish(kind, payload=None):
        calls.append((kind, payload))

    monkeypatch.setattr(run, "publish_task", fake_publish)

    response = run.app.test_client().post("/update-analysis")

    assert response.status_code == 202
    assert response.json["status"] == "queued"
    assert response.json["task"] == "recompute_analytics"
    assert calls[0][0] == "recompute_analytics"


@pytest.mark.buttons
def test_publish_failure_returns_503(monkeypatch):
    """Publish failures return service unavailable."""

    def bad_publish(_kind, payload=None):
        raise RuntimeError("rabbitmq unavailable")

    monkeypatch.setattr(run, "publish_task", bad_publish)

    response = run.app.test_client().post("/pull-data")

    assert response.status_code == 503
    assert response.json["error"] == "publish_failed"
@pytest.mark.buttons
def test_update_analysis_publish_failure_returns_503(monkeypatch):
    """Update Analysis publish failures return service unavailable."""

    def bad_publish(_kind, payload=None):
        raise RuntimeError("rabbitmq unavailable")

    monkeypatch.setattr(run, "publish_task", bad_publish)

    response = run.app.test_client().post("/update-analysis")

    assert response.status_code == 503
    assert response.json["error"] == "publish_failed"