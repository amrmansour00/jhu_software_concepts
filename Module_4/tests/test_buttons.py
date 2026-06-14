import pytest
from app import create_app, AppState


def fake_queries():
    return {"Q1 Fall 2026 entries": [(1,)]}


@pytest.mark.buttons
def test_pull_data_returns_ok_and_triggers_loader():
    calls = {"loader": 0}

    def fake_loader():
        calls["loader"] += 1
        return {"loaded": 2}

    app = create_app(
        query_function=fake_queries,
        loader_function=fake_loader
    )

    client = app.test_client()
    response = client.post("/pull-data")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert calls["loader"] == 1


@pytest.mark.buttons
def test_update_analysis_returns_ok_when_not_busy():
    app = create_app(query_function=fake_queries)
    client = app.test_client()

    response = client.post("/update-analysis")

    assert response.status_code == 200
    assert response.json["ok"] is True
    assert response.json["busy"] is False


@pytest.mark.buttons
def test_update_analysis_returns_409_when_busy():
    state = AppState()
    state.busy = True

    app = create_app(
        query_function=fake_queries,
        state=state
    )

    client = app.test_client()
    response = client.post("/update-analysis")

    assert response.status_code == 409
    assert response.json["busy"] is True


@pytest.mark.buttons
def test_pull_data_returns_409_when_busy():
    state = AppState()
    state.busy = True

    app = create_app(
        query_function=fake_queries,
        state=state
    )

    client = app.test_client()
    response = client.post("/pull-data")

    assert response.status_code == 409
    assert response.json["busy"] is True


@pytest.mark.buttons
def test_loader_error_returns_500():
    def bad_loader():
        raise RuntimeError("loader failed")

    app = create_app(
        query_function=fake_queries,
        loader_function=bad_loader
    )

    client = app.test_client()
    response = client.post("/pull-data")

    assert response.status_code == 500
    assert response.json["ok"] is False
    assert "loader failed" in response.json["message"]