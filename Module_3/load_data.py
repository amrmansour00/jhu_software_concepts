import os
import json
from pathlib import Path
from datetime import datetime

import psycopg
from dotenv import load_dotenv


BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR.parent / "Module_2" / "llm_extend_applicant_data.json"


def clean_float(value):
    try:
        if value in [None, "", "None"]:
            return None
        return float(value)
    except (ValueError, TypeError):
        return None


def clean_date(value):
    if not value:
        return None

    formats = ["%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


def create_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS applicants;

            CREATE TABLE applicants (
                p_id SERIAL PRIMARY KEY,
                program TEXT,
                comments TEXT,
                date_added DATE,
                url TEXT,
                status TEXT,
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
        """)
    conn.commit()


def load_json_data():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def insert_records(conn, records):
    insert_sql = """
        INSERT INTO applicants (
            program, comments, date_added, url, status, term,
            us_or_international, gpa, gre, gre_v, gre_aw, degree,
            llm_generated_program, llm_generated_university
        )
        VALUES (
            %(program)s, %(comments)s, %(date_added)s, %(url)s,
            %(status)s, %(term)s, %(us_or_international)s,
            %(gpa)s, %(gre)s, %(gre_v)s, %(gre_aw)s, %(degree)s,
            %(llm_generated_program)s, %(llm_generated_university)s
        );
    """

    loaded_count = 0
    batch_size = 500

    with conn.cursor() as cur:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            rows = []

            for record in batch:
                rows.append({
                    "program": record.get("program_name"),
                    "comments": record.get("comments"),
                    "date_added": clean_date(record.get("date_added")),
                    "url": record.get("entry_url"),
                    "status": record.get("applicant_status"),
                    "term": record.get("start_term"),
                    "us_or_international": record.get("student_type"),
                    "gpa": clean_float(record.get("gpa")),
                    "gre": clean_float(record.get("gre_score")),
                    "gre_v": clean_float(record.get("gre_v_score")),
                    "gre_aw": clean_float(record.get("gre_aw")),
                    "degree": record.get("degree"),
                    "llm_generated_program": record.get("standardized_program_name"),
                    "llm_generated_university": record.get("standardized_university"),
                })

            cur.executemany(insert_sql, rows)
            conn.commit()

            loaded_count += len(rows)
            print(f"Loaded {loaded_count} records...")

    return loaded_count


def main():
    load_dotenv()

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError("DATABASE_URL not found in .env")

    print("Connecting to PostgreSQL...")
    conn = psycopg.connect(database_url)

    print("Creating applicants table...")
    create_table(conn)

    print("Loading JSON data...")
    records = load_json_data()
    print(f"Found {len(records)} records in JSON file.")

    print("Inserting records into database...")
    loaded_count = insert_records(conn, records)

    conn.close()

    print(f"Loaded {loaded_count} records into applicants table.")


if __name__ == "__main__":
    main()