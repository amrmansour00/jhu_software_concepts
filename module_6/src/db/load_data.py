"""Database loading and analytics helpers for Module 6."""

import json
from pathlib import Path

import psycopg


CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS applicants (
    p_id SERIAL PRIMARY KEY,
    program TEXT NOT NULL,
    comments TEXT,
    date_added DATE,
    url TEXT UNIQUE NOT NULL,
    status TEXT NOT NULL,
    term TEXT,
    us_or_international TEXT,
    gpa FLOAT,
    gre FLOAT,
    gre_v FLOAT,
    gre_aw FLOAT,
    degree TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);

CREATE TABLE IF NOT EXISTS ingestion_watermarks (
    source TEXT PRIMARY KEY,
    last_seen TEXT,
    updated_at TIMESTAMPTZ DEFAULT now()
);
"""


INSERT_SQL = """
INSERT INTO applicants (
    program,
    comments,
    date_added,
    url,
    status,
    term,
    us_or_international,
    gpa,
    gre,
    gre_v,
    gre_aw,
    degree,
    llm_generated_program,
    llm_generated_university
)
VALUES (
    %(program)s,
    %(comments)s,
    %(date_added)s,
    %(url)s,
    %(status)s,
    %(term)s,
    %(us_or_international)s,
    %(gpa)s,
    %(gre)s,
    %(gre_v)s,
    %(gre_aw)s,
    %(degree)s,
    %(llm_generated_program)s,
    %(llm_generated_university)s
)
ON CONFLICT (url) DO NOTHING;
"""


def create_schema(connection):
    """Create database schema and watermark table."""
    with connection.cursor() as cursor:
        cursor.execute(CREATE_TABLES_SQL)


def normalize_record(record):
    """Normalize applicant record into database schema."""
    return {
        "program": record.get("program") or "Unknown",
        "comments": record.get("comments"),
        "date_added": record.get("date_added"),
        "url": record.get("url"),
        "status": record.get("status") or "Unknown",
        "term": record.get("term"),
        "us_or_international": record.get("us_or_international"),
        "gpa": record.get("gpa"),
        "gre": record.get("gre"),
        "gre_v": record.get("gre_v"),
        "gre_aw": record.get("gre_aw"),
        "degree": record.get("degree"),
        "llm_generated_program": record.get("llm_generated_program"),
        "llm_generated_university": record.get("llm_generated_university"),
    }


def load_seed_json(path):
    """Load applicant records from JSON file."""
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_watermark(connection, source):
    """Read last processed watermark."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT last_seen FROM ingestion_watermarks WHERE source = %s;",
            (source,),
        )
        row = cursor.fetchone()
    return row[0] if row else None


def update_watermark(connection, source, last_seen):
    """Update source watermark after successful processing."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ingestion_watermarks (source, last_seen)
            VALUES (%s, %s)
            ON CONFLICT (source)
            DO UPDATE SET last_seen = EXCLUDED.last_seen, updated_at = now();
            """,
            (source, last_seen),
        )


def insert_records(connection, records):
    """Insert applicant records idempotently."""
    inserted = 0

    with connection.cursor() as cursor:
        for record in records:
            normalized = normalize_record(record)
            if not normalized["url"]:
                continue

            cursor.execute(INSERT_SQL, normalized)
            inserted += cursor.rowcount

    return inserted


def handle_scrape_new_data(connection, json_path, source="gradcafe_seed"):
    """Load only records newer than watermark and advance watermark."""
    create_schema(connection)

    last_seen = get_watermark(connection, source)
    records = load_seed_json(json_path)

    new_records = []
    max_seen = last_seen

    for record in records:
        record_key = record.get("url")
        if last_seen is None or record_key > last_seen:
            new_records.append(record)
            max_seen = max(max_seen or record_key, record_key)

    inserted = insert_records(connection, new_records)

    if max_seen:
        update_watermark(connection, source, max_seen)

    return {"processed": len(new_records), "inserted": inserted}


def recompute_analytics(connection):
    """Placeholder for recomputing summaries used by the UI."""
    create_schema(connection)
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM applicants;")
        total = cursor.fetchone()[0]
    return {"applicant_count": total}


def query_analysis(connection):
    """Return UI-facing analytics."""
    create_schema(connection)

    queries = {
        "Q1 Fall 2026 entries": """
            SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026';
        """,
        "Q2 Percentage international students": """
            SELECT COALESCE(
                ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE us_or_international ILIKE '%International%'
                    ) / NULLIF(COUNT(*), 0),
                    2
                ),
                0
            )
            FROM applicants;
        """,
        "Q3 Average GPA": """
            SELECT COALESCE(ROUND(AVG(gpa)::numeric, 2), 0)
            FROM applicants;
        """,
    }

    results = {}
    with connection.cursor() as cursor:
        for question, statement in queries.items():
            cursor.execute(statement)
            results[question] = cursor.fetchall()

    return results