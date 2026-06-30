"""Query and formatting helpers for the Flask web service."""

from db.load_data import query_analysis


def run_queries(connection):
    """Run UI analytics queries."""
    return query_analysis(connection)


def format_results(raw_results):
    """Format SQL query rows for display."""
    formatted = {}

    for question, rows in raw_results.items():
        answers = []

        for row in rows:
            if len(row) == 1:
                answers.append(f"Answer: {row[0]}")
            else:
                answers.append(
                    "Answer: " + " | ".join(str(item) for item in row)
                )

        formatted[question] = answers

    return formatted