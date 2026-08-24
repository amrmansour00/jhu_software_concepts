"""Tests for Module 4 data-loading behavior."""

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

import load_data


@pytest.mark.db
def test_clean_float_valid_values():
    assert load_data.clean_float("3.75") == 3.75
    assert load_data.clean_float(325) == 325.0
    assert load_data.clean_float(4.5) == 4.5


@pytest.mark.db
def test_clean_float_missing_and_invalid_values():
    assert load_data.clean_float(None) is None
    assert load_data.clean_float("") is None
    assert load_data.clean_float("None") is None
    assert load_data.clean_float("not-a-number") is None


@pytest.mark.db
def test_clean_gpa():
    assert load_data.clean_gpa("3.8") == 3.8
    assert load_data.clean_gpa(None) is None
    assert load_data.clean_gpa("4.5") is None
    assert load_data.clean_gpa("-1") is None


@pytest.mark.db
def test_clean_gre():
    assert load_data.clean_gre("325") == 325.0
    assert load_data.clean_gre(None) is None
    assert load_data.clean_gre("250") is None
    assert load_data.clean_gre("350") is None


@pytest.mark.db
def test_clean_gre_verbal():
    assert load_data.clean_gre_verbal("160") == 160.0
    assert load_data.clean_gre_verbal(None) is None
    assert load_data.clean_gre_verbal("120") is None
    assert load_data.clean_gre_verbal("180") is None


@pytest.mark.db
def test_clean_gre_aw():
    assert load_data.clean_gre_aw("4.5") == 4.5
    assert load_data.clean_gre_aw(None) is None
    assert load_data.clean_gre_aw("-1") is None
    assert load_data.clean_gre_aw("7") is None


@pytest.mark.db
def test_clean_date_supported_formats():
    assert load_data.clean_date("2026-05-01") == date(2026, 5, 1)
    assert load_data.clean_date("May 01, 2026") == date(2026, 5, 1)
    assert load_data.clean_date("May 1, 2026") == date(2026, 5, 1)


@pytest.mark.db
def test_clean_date_missing_and_invalid_values():
    assert load_data.clean_date(None) is None
    assert load_data.clean_date("") is None
    assert load_data.clean_date("not-a-date") is None


@pytest.mark.db
def test_get_connection_uses_database_url():
    fake_conn = object()

    with patch.object(load_data, "load_dotenv"), \
         patch.object(load_data.os, "getenv", return_value="postgresql://test"), \
         patch.object(load_data.psycopg, "connect", return_value=fake_conn) as connect:
        result = load_data.get_connection()

    assert result is fake_conn
    connect.assert_called_once_with("postgresql://test")


@pytest.mark.db
def test_get_connection_requires_database_url():
    with patch.object(load_data, "load_dotenv"), \
         patch.object(load_data.os, "getenv", return_value=None):
        with pytest.raises(ValueError, match="DATABASE_URL"):
            load_data.get_connection()


@pytest.mark.db
def test_create_table_executes_schema_and_commits():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value

    load_data.create_table(conn)

    cursor.execute.assert_called_once()
    sql = cursor.execute.call_args.args[0]

    assert "CREATE TABLE IF NOT EXISTS applicants" in sql
    assert "url TEXT UNIQUE" in sql
    conn.commit.assert_called_once()


@pytest.mark.db
def test_load_json_data_reads_file():
    sample = '[{"program_name": "Computer Science"}]'

    with patch.object(Path, "exists", return_value=True), \
         patch("pathlib.Path.open", mock_open(read_data=sample)):
        result = load_data.load_json_data()

    assert result == [{"program_name": "Computer Science"}]


@pytest.mark.db
def test_load_json_data_missing_file():
    with patch.object(Path, "exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            load_data.load_json_data()


@pytest.mark.db
def test_prepare_record_maps_module2_fields():
    source = {
        "program_name": "Computer Science",
        "comments": "Test applicant",
        "date_added": "2026-05-01",
        "entry_url": "https://example.com/result/1",
        "applicant_status": "Accepted",
        "start_term": "Fall 2026",
        "student_type": "International",
        "gpa": "3.80",
        "gre_score": "325",
        "gre_v_score": "160",
        "gre_aw": "4.5",
        "degree": "Masters",
        "standardized_program_name": "Computer Science",
        "standardized_university": "Johns Hopkins University",
    }

    row = load_data.prepare_record(source)

    assert row["program"] == "Computer Science"
    assert row["comments"] == "Test applicant"
    assert row["date_added"] == date(2026, 5, 1)
    assert row["url"] == "https://example.com/result/1"
    assert row["status"] == "Accepted"
    assert row["term"] == "Fall 2026"
    assert row["us_or_international"] == "International"
    assert row["gpa"] == 3.8
    assert row["gre"] == 325.0
    assert row["gre_v"] == 160.0
    assert row["gre_aw"] == 4.5
    assert row["degree"] == "Masters"
    assert row["llm_generated_program"] == "Computer Science"
    assert row["llm_generated_university"] == "Johns Hopkins University"


@pytest.mark.db
def test_prepare_record_filters_invalid_scores():
    source = {
        "entry_url": "https://example.com/result/2",
        "gpa": "99.99",
        "gre_score": "99.99",
        "gre_v_score": "999",
        "gre_aw": "99.99",
    }

    row = load_data.prepare_record(source)

    assert row["gpa"] is None
    assert row["gre"] is None
    assert row["gre_v"] is None
    assert row["gre_aw"] is None


@pytest.mark.db
def test_insert_records_skips_missing_url_and_batches():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value

    records = [
        {
            "entry_url": "https://example.com/1",
            "program_name": "Computer Science",
        },
        {
            "entry_url": None,
            "program_name": "No URL",
        },
    ]

    count = load_data.insert_records(conn, records)

    assert count == 1
    cursor.executemany.assert_called_once()
    conn.commit.assert_called_once()


@pytest.mark.db
def test_insert_records_handles_multiple_batches():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value

    records = [
        {
            "entry_url": f"https://example.com/{i}",
            "program_name": "Computer Science",
        }
        for i in range(501)
    ]

    count = load_data.insert_records(conn, records)

    assert count == 501
    assert cursor.executemany.call_count == 2
    assert conn.commit.call_count == 2


@pytest.mark.db
def test_get_database_statistics():
    conn = MagicMock()
    cursor = conn.cursor.return_value.__enter__.return_value

    cursor.fetchone.side_effect = [
        (14805, 14805),
        (0,),
        (0,),
        (0,),
    ]

    stats = load_data.get_database_statistics(conn)

    assert stats["total_records"] == 14805
    assert stats["unique_urls"] == 14805
    assert stats["invalid_gre"] == 0
    assert stats["invalid_gre_v"] == 0
    assert stats["invalid_gre_aw"] == 0


@pytest.mark.db
def test_main_success(capsys):
    conn = MagicMock()

    with patch.object(load_data, "get_connection", return_value=conn), \
         patch.object(load_data, "create_table"), \
         patch.object(load_data, "load_json_data", return_value=[{"entry_url": "x"}]), \
         patch.object(load_data, "insert_records", return_value=1), \
         patch.object(
             load_data,
             "get_database_statistics",
             return_value={
                 "total_records": 1,
                 "unique_urls": 1,
                 "invalid_gre": 0,
                 "invalid_gre_v": 0,
                 "invalid_gre_aw": 0,
             },
         ):
        load_data.main()

    output = capsys.readouterr().out

    assert "DATABASE LOAD COMPLETE" in output
    assert "Duplicate URL validation: PASSED" in output
    conn.close.assert_called_once()


@pytest.mark.db
def test_main_duplicate_validation_failed(capsys):
    conn = MagicMock()

    with patch.object(load_data, "get_connection", return_value=conn), \
         patch.object(load_data, "create_table"), \
         patch.object(load_data, "load_json_data", return_value=[{"entry_url": "x"}]), \
         patch.object(load_data, "insert_records", return_value=1), \
         patch.object(
             load_data,
             "get_database_statistics",
             return_value={
                 "total_records": 2,
                 "unique_urls": 1,
                 "invalid_gre": 0,
                 "invalid_gre_v": 0,
                 "invalid_gre_aw": 0,
             },
         ):
        load_data.main()

    output = capsys.readouterr().out

    assert "Duplicate URL validation: FAILED" in output
    conn.close.assert_called_once()