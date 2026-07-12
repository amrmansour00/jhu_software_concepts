"""Button and busy-state behavior tests."""

import pytest

from app import AppState, create_app


def fake_queries(limit=10):
    """Return fake analysis results."""
    return {"Q1 Fall 2026 entries": [(limit,)]}


@pytest.mark.buttons
def test_pull_data_returns_ok_and_triggers_loader():
    """Verify Pull Data calls the loader."""
    calls = {"loader": 0}

    def fake_loader():
        calls["loader"] += 1
        return {"loaded": 2}

    app = create_app(
        query_function=fake_queries,
        loader_function=fake_loader,
    )

    response = app.test_client().post("/pull-data")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert calls["loader"] == 1


@pytest.mark.buttons
def test_update_analysis_returns_ok_when_not_busy():
    """Verify Update Analysis succeeds when not busy."""
    app = create_app(query_function=fake_queries)

    response = app.test_client().post("/update-analysis")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["busy"] is False


@pytest.mark.buttons
def test_update_analysis_returns_busy_response():
    """Verify Update Analysis is blocked while a data pull is running."""
    state = AppState()
    state.busy = True

    app = create_app(
        query_function=fake_queries,
        state=state,
    )

    response = app.test_client().post("/update-analysis")

    assert response.status_code == 409
    assert response.json["busy"] is True


@pytest.mark.buttons
def test_pull_data_returns_busy_response():
    """Verify Pull Data is blocked while already running."""
    state = AppState()
    state.busy = True

    app = create_app(
        query_function=fake_queries,
        state=state,
    )

    response = app.test_client().post("/pull-data")

    assert response.status_code == 409
    assert response.json["busy"] is True


@pytest.mark.buttons
def test_loader_error_returns_500():
    """Verify loader failures return HTTP 500."""

    def bad_loader():
        raise RuntimeError("loader failed")

    app = create_app(
        query_function=fake_queries,
        loader_function=bad_loader,
    )

    response = app.test_client().post("/pull-data")

    assert response.status_code == 500
    assert response.json["ok"] is False
    assert "loader failed" in response.json["message"]