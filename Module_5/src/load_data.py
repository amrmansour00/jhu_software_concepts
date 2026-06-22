"""Data loading helpers for the GradCafe PostgreSQL database."""

from psycopg import sql

from db import get_connection


REQUIRED_COLUMNS = [
    "program",
    "comments",
    "date_added",
    "url",
    "status",
    "term",
    "us_or_international",
    "gpa",
    "gre",
    "gre_v",
    "gre_aw",
    "degree",
    "llm_generated_program",
    "llm_generated_university",
]


CREATE_TABLE_SQL = """
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
"""


def create_applicants_table(connection):
    """Create the applicants table with the required schema."""
    with connection.cursor() as cursor:
        cursor.execute(CREATE_TABLE_SQL)
    connection.commit()


def normalize_record(record):
    """Normalize a source record to the applicants table schema."""
    return {
        "program": record.get("program") or record.get("program_name") or "Unknown",
        "comments": record.get("comments"),
        "date_added": record.get("date_added"),
        "url": record.get("url") or record.get("entry_url"),
        "status": record.get("status") or record.get("applicant_status") or "Unknown",
        "term": record.get("term") or record.get("start_term"),
        "us_or_international": (
            record.get("us_or_international")
            or record.get("student_type")
        ),
        "gpa": record.get("gpa"),
        "gre": record.get("gre") or record.get("gre_score"),
        "gre_v": record.get("gre_v") or record.get("gre_v_score"),
        "gre_aw": record.get("gre_aw"),
        "degree": record.get("degree"),
        "llm_generated_program": (
            record.get("llm_generated_program")
            or record.get("standardized_program_name")
        ),
        "llm_generated_university": (
            record.get("llm_generated_university")
            or record.get("standardized_university")
        ),
    }


def validate_record(record):
    """Validate required non-null fields before insert."""
    required = ["program", "url", "status"]

    missing = [
        field for field in required
        if not record.get(field)
    ]

    if missing:
        raise ValueError(
            "Missing required applicant fields: "
            + ", ".join(missing)
        )


def insert_applicant(connection, record):
    """Insert one applicant safely and idempotently."""
    normalized = normalize_record(record)
    validate_record(normalized)

    columns = [sql.Identifier(column) for column in REQUIRED_COLUMNS]
    placeholders = [sql.Placeholder(column) for column in REQUIRED_COLUMNS]

    statement = sql.SQL(
        """
        INSERT INTO applicants ({columns})
        VALUES ({values})
        ON CONFLICT (url) DO NOTHING;
        """
    ).format(
        columns=sql.SQL(", ").join(columns),
        values=sql.SQL(", ").join(placeholders),
    )

    with connection.cursor() as cursor:
        cursor.execute(statement, normalized)

    connection.commit()


def load_records(records, connection_factory=get_connection):
    """Load records into PostgreSQL and return the attempted count."""
    with connection_factory() as connection:
        create_applicants_table(connection)

        for record in records:
            insert_applicant(connection, record)

    return len(records)
