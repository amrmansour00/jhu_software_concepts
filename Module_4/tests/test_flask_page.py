import pytest
from bs4 import BeautifulSoup
from app import create_app


def fake_queries():
    return {
        "Q1 Fall 2026 entries": [(14611,)],
        "Q2 Percentage international students": [("23.60%",)],
    }


@pytest.mark.web
def test_create_app_has_required_routes():
    app = create_app(query_function=fake_queries)
    routes = [rule.rule for rule in app.url_map.iter_rules()]

    assert "/" in routes
    assert "/analysis" in routes
    assert "/pull-data" in routes
    assert "/update-analysis" in routes


@pytest.mark.web
def test_analysis_page_loads_and_renders_required_components():
    app = create_app(query_function=fake_queries)
    client = app.test_client()

    response = client.get("/analysis")

    assert response.status_code == 200

    soup = BeautifulSoup(response.data, "html.parser")
    page_text = soup.get_text()

    assert "Analysis" in page_text
    assert "Pull Data" in page_text
    assert "Update Analysis" in page_text
    assert "Answer:" in page_text
    assert soup.find(attrs={"data-testid": "pull-data-btn"}) is not None
    assert soup.find(attrs={"data-testid": "update-analysis-btn"}) is not None

@pytest.mark.web
def test_format_results_handles_empty_rows():
    from app import format_results

    raw_results = {
        "Empty result": []
    }

    formatted = format_results(raw_results)

    assert formatted == {
        "Empty result": []
    }


@pytest.mark.web
def test_default_loader_is_used():
    app = create_app(query_function=fake_queries)
    client = app.test_client()

    response = client.post("/pull-data")

    assert response.status_code == 200
    assert response.json["result"] == {"loaded": 0}