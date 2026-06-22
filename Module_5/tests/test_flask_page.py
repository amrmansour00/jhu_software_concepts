"""Flask page rendering tests."""

import pytest
from bs4 import BeautifulSoup

from app import create_app


def fake_queries(limit=10):
    """Return fake analysis results."""
    return {
        "Q1 Fall 2026 entries": [(limit,)],
        "Q2 Percentage international students": [("23.60%",)],
    }


@pytest.mark.web
def test_create_app_has_required_routes():
    """Verify required Flask routes exist."""
    app = create_app(query_function=fake_queries)
    routes = [rule.rule for rule in app.url_map.iter_rules()]

    assert "/" in routes
    assert "/analysis" in routes
    assert "/pull-data" in routes
    assert "/update-analysis" in routes


@pytest.mark.web
def test_analysis_page_loads_required_components():
    """Verify GET /analysis returns required HTML components."""
    app = create_app(query_function=fake_queries)
    client = app.test_client()

    response = client.get("/analysis?limit=5000")

    soup = BeautifulSoup(response.data, "html.parser")
    page_text = soup.get_text()

    assert response.status_code == 200
    assert "Analysis" in page_text
    assert "Pull Data" in page_text
    assert "Update Analysis" in page_text
    assert "Answer:" in page_text
    assert "Answer: 100" in page_text
    assert soup.find(attrs={"data-testid": "pull-data-btn"}) is not None
    assert soup.find(attrs={"data-testid": "update-analysis-btn"}) is not None