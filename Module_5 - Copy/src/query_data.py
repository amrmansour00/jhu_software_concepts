"""Safe SQL query functions for GradCafe analysis."""

from psycopg import sql

from db import get_connection


MIN_LIMIT = 1
MAX_LIMIT = 100


QUERY_DEFINITIONS = {
    "Q1 Fall 2026 entries": {
        "statement": """
            SELECT COUNT(*)
            FROM applicants
            WHERE term = %s
            LIMIT %s;
        """,
        "params": ("Fall 2026",),
    },
    "Q2 Percentage international students": {
        "statement": """
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE us_or_international ILIKE %s
                ) / NULLIF(COUNT(*), 0),
                2
            )
            FROM applicants
            LIMIT %s;
        """,
        "params": ("%International%",),
    },
    "Q3 Average GPA, GRE, GRE V, GRE AW": {
        "statement": """
            SELECT
                ROUND(AVG(gpa)::numeric, 2),
                ROUND(AVG(gre)::numeric, 2),
                ROUND(AVG(gre_v)::numeric, 2),
                ROUND(AVG(gre_aw)::numeric, 2)
            FROM applicants
            LIMIT %s;
        """,
        "params": (),
    },
    "Q4 Average GPA of American students in Fall 2026": {
        "statement": """
            SELECT ROUND(AVG(gpa)::numeric, 2)
            FROM applicants
            WHERE term = %s
              AND us_or_international ILIKE %s
            LIMIT %s;
        """,
        "params": ("Fall 2026", "%American%"),
    },
    "Q5 Percentage Fall 2026 acceptances": {
        "statement": """
            SELECT ROUND(
                100.0 * COUNT(*) FILTER (
                    WHERE status ILIKE %s
                ) / NULLIF(COUNT(*), 0),
                2
            )
            FROM applicants
            WHERE term = %s
            LIMIT %s;
        """,
        "params": ("%Accepted%", "Fall 2026"),
    },
}


def clamp_limit(limit_value):
    """Clamp limit values to the allowed safe range."""
    try:
        limit = int(limit_value)
    except (TypeError, ValueError):
        return 10

    return max(MIN_LIMIT, min(limit, MAX_LIMIT))


def build_statement(statement_text):
    """Build a psycopg SQL object from static SQL text."""
    return sql.SQL(statement_text)


def execute_query(cursor, statement_text, params, limit_value):
    """Execute a safe SQL query with bound parameters."""
    safe_limit = clamp_limit(limit_value)
    statement = build_statement(statement_text)
    cursor.execute(statement, (*params, safe_limit))
    return cursor.fetchall()


def run_queries(limit=10, connection_factory=get_connection):
    """Run all analysis queries and return a result dictionary."""
    results = {}

    with connection_factory() as connection:
        with connection.cursor() as cursor:
            for question, query in QUERY_DEFINITIONS.items():
                results[question] = execute_query(
                    cursor,
                    query["statement"],
                    query["params"],
                    limit,
                )

    return results


def expected_result_keys():
    """Return expected analysis keys used by the template."""
    return list(QUERY_DEFINITIONS.keys())


def print_results(results):
    """Print query results to the terminal."""
    print("\nGradCafe SQL Analysis Results")
    print("=" * 40)

    for question, rows in results.items():
        print(f"\n{question}")
        print("-" * len(question))

        for row in rows:
            print(row)


if __name__ == "__main__":  # pragma: no cover
    print_results(run_queries())
