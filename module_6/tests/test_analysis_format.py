"""Analysis formatting tests."""

import re

import pytest
from bs4 import BeautifulSoup

from app import create_app, format_results


def fake_queries(limit=10):
    """Return percentage results."""
    return {
        "Q2 Percentage international students": [("23.60%",)],
        "Q5 Percentage Fall 2026 acceptances": [("40.76%",)],
    }


@pytest.mark.analysis
def test_analysis_answers_are_labeled():
    """Verify each analysis output is labeled with Answer."""
    app = create_app(query_function=fake_queries)
    response = app.test_client().get("/analysis")

    soup = BeautifulSoup(response.data, "html.parser")
    answers = soup.find_all(class_="answer")

    assert answers
    assert all("Answer:" in answer.get_text() for answer in answers)


@pytest.mark.analysis
def test_percentages_have_two_decimal_places():
    """Verify percentages are rendered with two decimals."""
    app = create_app(query_function=fake_queries)
    response = app.test_client().get("/analysis")
    text = response.data.decode("utf-8")

    percentages = re.findall(r"\d+\.\d{2}%", text)

    assert "23.60%" in percentages
    assert "40.76%" in percentages


@pytest.mark.analysis
def test_format_results_handles_multi_value_rows():
    """Verify multi-value rows are formatted consistently."""
    formatted = format_results(
        {"Multi value result": [("GPA", "3.77", "GRE", "253.97")]}
    )

    assert formatted["Multi value result"] == [
        "Answer: GPA | 3.77 | GRE | 253.97"
    ]