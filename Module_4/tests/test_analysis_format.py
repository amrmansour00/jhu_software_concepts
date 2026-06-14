import re
import pytest
from bs4 import BeautifulSoup
from app import create_app


def fake_queries():
    return {
        "Q2 Percentage international students": [("23.60%",)],
        "Q5 Percentage Fall 2026 acceptances": [("40.76%",)],
    }


@pytest.mark.analysis
def test_analysis_answers_are_labeled():
    app = create_app(query_function=fake_queries)
    client = app.test_client()

    response = client.get("/analysis")

    soup = BeautifulSoup(response.data, "html.parser")
    answers = soup.find_all(class_="answer")

    assert len(answers) >= 1
    assert all("Answer:" in answer.get_text() for answer in answers)


@pytest.mark.analysis
def test_percentages_have_two_decimal_places():
    app = create_app(query_function=fake_queries)
    client = app.test_client()

    response = client.get("/analysis")
    text = response.data.decode("utf-8")

    percentages = re.findall(r"\d+\.\d{2}%", text)

    assert "23.60%" in percentages
    assert "40.76%" in percentages

@pytest.mark.analysis
def test_format_results_handles_multiple_values():
    from app import format_results

    raw_results = {
        "Multi value result": [("GPA", "3.77", "GRE", "253.97")]
    }

    formatted = format_results(raw_results)

    assert formatted["Multi value result"] == [
        "Answer: GPA | 3.77 | GRE | 253.97"
    ]