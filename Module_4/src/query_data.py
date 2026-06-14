import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"

load_dotenv(ENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")


QUERIES = {
    "Q1 Fall 2026 entries": """
        SELECT COUNT(*)
        FROM applicants
        WHERE term = 'Fall 2026';
    """,

    "Q2 Percentage international students": """
        SELECT ROUND(
            100.0 * COUNT(*) FILTER (
                WHERE us_or_international ILIKE '%International%'
            ) / NULLIF(COUNT(*), 0),
            2
        )
        FROM applicants;
    """,

    "Q3 Average GPA, GRE, GRE V, GRE AW": """
        SELECT
            ROUND(AVG(gpa)::numeric, 2),
            ROUND(AVG(gre)::numeric, 2),
            ROUND(AVG(gre_v)::numeric, 2),
            ROUND(AVG(gre_aw)::numeric, 2)
        FROM applicants;
    """,

    "Q4 Average GPA of American students in Fall 2026": """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE term = 'Fall 2026'
          AND us_or_international ILIKE '%American%';
    """,

    "Q5 Percentage Fall 2026 acceptances": """
        SELECT ROUND(
            100.0 * COUNT(*) FILTER (
                WHERE status ILIKE '%Accepted%'
            ) / NULLIF(COUNT(*), 0),
            2
        )
        FROM applicants
        WHERE term = 'Fall 2026';
    """,

    "Q6 Average GPA of Fall 2026 acceptances": """
        SELECT ROUND(AVG(gpa)::numeric, 2)
        FROM applicants
        WHERE term = 'Fall 2026'
          AND status ILIKE '%Accepted%';
    """,

    "Q7 JHU Masters Computer Science entries": """
        SELECT COUNT(*)
        FROM applicants
        WHERE degree ILIKE '%Master%'
          AND (
                program ILIKE '%Johns Hopkins%'
             OR program ILIKE '%JHU%'
             OR llm_generated_university ILIKE '%Johns Hopkins%'
          )
          AND (
                program ILIKE '%Computer Science%'
             OR llm_generated_program ILIKE '%Computer Science%'
          );
    """,

    "Q8 2026 CS PhD acceptances from selected universities using scraped fields": """
        SELECT COUNT(*)
        FROM applicants
        WHERE status ILIKE '%Accepted%'
          AND degree ILIKE '%PhD%'
          AND (
                term ILIKE '%2026%'
             OR date_added BETWEEN '2026-01-01' AND '2026-12-31'
          )
          AND program ILIKE '%Computer Science%'
          AND (
                program ILIKE '%Georgetown%'
             OR program ILIKE '%MIT%'
             OR program ILIKE '%Massachusetts Institute of Technology%'
             OR program ILIKE '%Stanford%'
             OR program ILIKE '%Carnegie Mellon%'
          );
    """,

    "Q9 Same as Q8 using LLM-generated fields": """
        SELECT COUNT(*)
        FROM applicants
        WHERE status ILIKE '%Accepted%'
          AND degree ILIKE '%PhD%'
          AND (
                term ILIKE '%2026%'
             OR date_added BETWEEN '2026-01-01' AND '2026-12-31'
          )
          AND llm_generated_program ILIKE '%Computer Science%'
          AND (
                llm_generated_university ILIKE '%Georgetown%'
             OR llm_generated_university ILIKE '%Massachusetts Institute of Technology%'
             OR llm_generated_university ILIKE '%MIT%'
             OR llm_generated_university ILIKE '%Stanford%'
             OR llm_generated_university ILIKE '%Carnegie Mellon%'
          );
    """,

    "Q10 Original question: Top 10 universities by acceptance count": """
        SELECT llm_generated_university, COUNT(*) AS acceptance_count
        FROM applicants
        WHERE status ILIKE '%Accepted%'
          AND llm_generated_university IS NOT NULL
        GROUP BY llm_generated_university
        ORDER BY acceptance_count DESC
        LIMIT 10;
    """,

    "Q11 Original question: Average GPA by degree type": """
        SELECT degree, ROUND(AVG(gpa)::numeric, 2) AS average_gpa, COUNT(*) AS entries
        FROM applicants
        WHERE gpa IS NOT NULL
          AND degree IS NOT NULL
        GROUP BY degree
        ORDER BY average_gpa DESC;
    """
}


def run_queries():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not found in .env")

    conn = psycopg.connect(DATABASE_URL)

    results = {}

    with conn.cursor() as cur:
        for question, sql in QUERIES.items():
            cur.execute(sql)
            rows = cur.fetchall()
            results[question] = rows

    conn.close()
    return results


def print_results(results):
    print("\nGradCafe SQL Analysis Results")
    print("=" * 40)

    for question, rows in results.items():
        print(f"\n{question}")
        print("-" * len(question))

        for row in rows:
            print(row)


if __name__ == "__main__":
    results = run_queries()
    print_results(results)