import json
import os
from datetime import datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv


# =========================================================
# PATH CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent

DATA_FILE = (
    REPO_DIR
    / "Module_2"
    / "llm_extend_applicant_data.json"
)


# =========================================================
# DATA CLEANING FUNCTIONS
# =========================================================

def clean_float(value):
    """
    Convert a value to float when possible.

    Missing or invalid values are returned as None so that
    PostgreSQL stores them as NULL.
    """
    try:
        if value in (None, "", "None"):
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


def clean_gpa(value):
    """
    Return a valid GPA value or None.

    GradCafe GPA values are expected to use a conventional
    0.0-4.0 scale for this analysis.
    """
    score = clean_float(value)

    if score is None:
        return None

    if 0 <= score <= 4:
        return score

    return None


def clean_gre(value):
    """
    Return a valid GRE total score or None.

    The current GRE Verbal and Quantitative sections each
    range from 130-170, giving a combined range of 260-340.
    """
    score = clean_float(value)

    if score is None:
        return None

    if 260 <= score <= 340:
        return score

    return None


def clean_gre_verbal(value):
    """
    Return a valid GRE Verbal score or None.

    GRE Verbal Reasoning scores range from 130-170.
    """
    score = clean_float(value)

    if score is None:
        return None

    if 130 <= score <= 170:
        return score

    return None


def clean_gre_aw(value):
    """
    Return a valid GRE Analytical Writing score or None.

    GRE Analytical Writing scores range from 0-6.
    Values outside this range are treated as invalid.
    """
    score = clean_float(value)

    if score is None:
        return None

    if 0 <= score <= 6:
        return score

    return None


def clean_date(value):
    """
    Convert supported date strings to a Python date object.
    """
    if not value:
        return None

    formats = (
        "%Y-%m-%d",
        "%b %d, %Y",
        "%B %d, %Y",
    )

    for fmt in formats:
        try:
            return datetime.strptime(
                str(value),
                fmt,
            ).date()

        except ValueError:
            continue

    return None


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    """
    Create a PostgreSQL connection using DATABASE_URL
    stored in Module_3/.env.
    """
    load_dotenv(BASE_DIR / ".env")

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL not found in Module_3/.env"
        )

    return psycopg.connect(database_url)


# =========================================================
# DATABASE TABLE
# =========================================================

def create_table(conn):
    """
    Create the applicants table if it does not already exist.

    The applicant URL is UNIQUE and acts as the natural
    de-duplication key.
    """
    create_sql = """
        CREATE TABLE IF NOT EXISTS applicants (
            p_id SERIAL PRIMARY KEY,
            program TEXT,
            comments TEXT,
            date_added DATE,
            url TEXT UNIQUE,
            status TEXT,
            term TEXT,
            us_or_international TEXT,
            gpa DOUBLE PRECISION,
            gre DOUBLE PRECISION,
            gre_v DOUBLE PRECISION,
            gre_aw DOUBLE PRECISION,
            degree TEXT,
            llm_generated_program TEXT,
            llm_generated_university TEXT
        );
    """

    with conn.cursor() as cur:
        cur.execute(create_sql)

    conn.commit()


# =========================================================
# LOAD MODULE 2 DATA
# =========================================================

def load_json_data():
    """
    Load the standardized applicant dataset produced by
    Module 2.
    """
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "Module 2 standardized dataset not found: "
            f"{DATA_FILE}"
        )

    with DATA_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# =========================================================
# RECORD PREPARATION
# =========================================================

def prepare_record(record):
    """
    Map a Module 2 JSON record to the Module 3 PostgreSQL
    schema and validate numeric fields.
    """
    return {
        "program": record.get("program_name"),

        "comments": record.get("comments"),

        "date_added": clean_date(
            record.get("date_added")
        ),

        "url": record.get("entry_url"),

        "status": record.get(
            "applicant_status"
        ),

        "term": record.get(
            "start_term"
        ),

        "us_or_international": record.get(
            "student_type"
        ),

        "gpa": clean_gpa(
            record.get("gpa")
        ),

        "gre": clean_gre(
            record.get("gre_score")
        ),

        "gre_v": clean_gre_verbal(
            record.get("gre_v_score")
        ),

        "gre_aw": clean_gre_aw(
            record.get("gre_aw")
        ),

        "degree": record.get(
            "degree"
        ),

        "llm_generated_program": record.get(
            "standardized_program_name"
        ),

        "llm_generated_university": record.get(
            "standardized_university"
        ),
    }


# =========================================================
# INSERT / UPDATE DATABASE RECORDS
# =========================================================

def insert_records(conn, records):
    """
    Insert or update applicant records.

    entry_url is used as the natural de-duplication key.
    Existing records with the same URL are updated rather
    than inserted again.
    """

    insert_sql = """
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
        ON CONFLICT (url)
        DO UPDATE SET
            program = EXCLUDED.program,
            comments = EXCLUDED.comments,
            date_added = EXCLUDED.date_added,
            status = EXCLUDED.status,
            term = EXCLUDED.term,
            us_or_international =
                EXCLUDED.us_or_international,
            gpa = EXCLUDED.gpa,
            gre = EXCLUDED.gre,
            gre_v = EXCLUDED.gre_v,
            gre_aw = EXCLUDED.gre_aw,
            degree = EXCLUDED.degree,
            llm_generated_program =
                EXCLUDED.llm_generated_program,
            llm_generated_university =
                EXCLUDED.llm_generated_university;
    """

    prepared = []

    skipped_missing_url = 0

    for record in records:
        row = prepare_record(record)

        # URL is required for deterministic de-duplication.
        if not row["url"]:
            skipped_missing_url += 1
            continue

        prepared.append(row)

    print(
        f"Records with usable URLs: "
        f"{len(prepared):,}"
    )

    if skipped_missing_url:
        print(
            f"Records skipped due to missing URL: "
            f"{skipped_missing_url:,}"
        )

    batch_size = 500
    processed_count = 0

    with conn.cursor() as cur:

        for start in range(
            0,
            len(prepared),
            batch_size,
        ):

            batch = prepared[
                start:start + batch_size
            ]

            cur.executemany(
                insert_sql,
                batch,
            )

            conn.commit()

            processed_count += len(batch)

            print(
                f"Processed {processed_count:,} "
                f"of {len(prepared):,} records..."
            )

    return processed_count


# =========================================================
# DATABASE VALIDATION
# =========================================================

def get_database_statistics(conn):
    """
    Return database counts used to verify that records are
    unique and numeric values passed validation.
    """

    with conn.cursor() as cur:

        cur.execute(
            """
            SELECT
                COUNT(*),
                COUNT(DISTINCT url)
            FROM applicants
            WHERE url IS NOT NULL;
            """
        )

        total_records, unique_urls = cur.fetchone()

        cur.execute(
            """
            SELECT COUNT(*)
            FROM applicants
            WHERE gre_aw IS NOT NULL
              AND (gre_aw < 0 OR gre_aw > 6);
            """
        )

        invalid_gre_aw = cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(*)
            FROM applicants
            WHERE gre IS NOT NULL
              AND (gre < 260 OR gre > 340);
            """
        )

        invalid_gre = cur.fetchone()[0]

        cur.execute(
            """
            SELECT COUNT(*)
            FROM applicants
            WHERE gre_v IS NOT NULL
              AND (gre_v < 130 OR gre_v > 170);
            """
        )

        invalid_gre_v = cur.fetchone()[0]

    return {
        "total_records": total_records,
        "unique_urls": unique_urls,
        "invalid_gre": invalid_gre,
        "invalid_gre_v": invalid_gre_v,
        "invalid_gre_aw": invalid_gre_aw,
    }


# =========================================================
# MAIN
# =========================================================

def main():

    print("Connecting to PostgreSQL...")

    conn = get_connection()

    try:

        print(
            "Ensuring applicants table exists..."
        )

        create_table(conn)

        print(
            "Loading standardized data from:"
        )

        print(DATA_FILE)

        records = load_json_data()

        print(
            f"Source records: {len(records):,}"
        )

        processed_count = insert_records(
            conn,
            records,
        )

        statistics = get_database_statistics(
            conn
        )

        print()
        print("DATABASE LOAD COMPLETE")
        print("=" * 60)

        print(
            f"Records processed: "
            f"{processed_count:,}"
        )

        print(
            f"Database records: "
            f"{statistics['total_records']:,}"
        )

        print(
            f"Unique URLs: "
            f"{statistics['unique_urls']:,}"
        )

        print(
            f"Invalid GRE totals remaining: "
            f"{statistics['invalid_gre']:,}"
        )

        print(
            f"Invalid GRE Verbal values remaining: "
            f"{statistics['invalid_gre_v']:,}"
        )

        print(
            f"Invalid GRE AW values remaining: "
            f"{statistics['invalid_gre_aw']:,}"
        )

        if (
            statistics["total_records"]
            == statistics["unique_urls"]
        ):
            print(
                "Duplicate URL validation: PASSED"
            )
        else:
            print(
                "Duplicate URL validation: FAILED"
            )

        print(
            "Existing URLs were updated rather "
            "than duplicated."
        )

    finally:
        conn.close()


# =========================================================
# COMMAND-LINE ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()