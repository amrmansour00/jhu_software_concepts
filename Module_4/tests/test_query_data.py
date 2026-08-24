"""Tests for query_data behavior without requiring a live database."""

from unittest.mock import MagicMock, patch

import pytest

import query_data


@pytest.mark.analysis
def test_queries_contains_expected_questions():
    assert len(query_data.QUERIES) == 11
    assert "Q1 Fall 2026 entries" in query_data.QUERIES
    assert "Q11 Original question: Average GPA by degree type" in query_data.QUERIES


@pytest.mark.analysis
def test_run_queries_returns_expected_dictionary():
    fake_cursor = MagicMock()

    fake_cursor.fetchall.side_effect = [
        [(14610,)],
        [(47.02,)],
        [(3.75, 324.79, 160.49, 4.33)],
        [(3.76,)],
        [(40.77,)],
        [(3.74,)],
        [(6,)],
        [(0,)],
        [(1,)],
        [("University of Oxford", 152)],
        [("Masters", 3.71, 3763)],
    ]

    fake_connection = MagicMock()
    fake_connection.cursor.return_value.__enter__.return_value = fake_cursor

    with patch.object(
        query_data,
        "DATABASE_URL",
        "postgresql://test"
    ):
        with patch.object(
            query_data.psycopg,
            "connect",
            return_value=fake_connection
        ):
            results = query_data.run_queries()

    assert len(results) == 11
    assert results["Q1 Fall 2026 entries"] == [(14610,)]
    assert results["Q7 JHU Masters Computer Science entries"] == [(6,)]
    assert (
        results["Q9 Same as Q8 using LLM-generated fields"]
        == [(1,)]
    )

    assert fake_cursor.execute.call_count == 11
    fake_connection.close.assert_called_once()


@pytest.mark.analysis
def test_run_queries_requires_database_url():
    with patch.object(
        query_data,
        "DATABASE_URL",
        None
    ):
        with pytest.raises(
            ValueError,
            match="DATABASE_URL not found"
        ):
            query_data.run_queries()


@pytest.mark.analysis
def test_print_results_outputs_question_and_rows(capsys):
    results = {
        "Q1 Fall 2026 entries": [(14610,)],
        "Q2 Percentage international students": [(47.02,)],
    }

    query_data.print_results(results)

    output = capsys.readouterr().out

    assert "GradCafe SQL Analysis Results" in output
    assert "Q1 Fall 2026 entries" in output
    assert "14610" in output
    assert "47.02" in output