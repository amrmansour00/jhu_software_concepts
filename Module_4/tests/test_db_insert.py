import pytest


REQUIRED_KEYS = {
    "p_id",
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
}


class FakeDatabase:
    def __init__(self):
        self.rows = {}

    def insert(self, row):
        self.rows[row["url"]] = row

    def count(self):
        return len(self.rows)

    def query_one(self):
        return next(iter(self.rows.values()))


@pytest.mark.db
def test_insert_on_pull_adds_required_row():
    db = FakeDatabase()

    row = {
        "p_id": 1,
        "program": "Computer Science",
        "comments": "Test row",
        "date_added": "2026-05-01",
        "url": "https://example.com/1",
        "status": "Accepted",
        "term": "Fall 2026",
        "us_or_international": "American",
        "gpa": 3.8,
        "gre": 165.0,
        "gre_v": 160.0,
        "gre_aw": 4.5,
        "degree": "Masters",
        "llm_generated_program": "Computer Science",
        "llm_generated_university": "Johns Hopkins University",
    }

    db.insert(row)

    assert db.count() == 1
    assert set(db.query_one().keys()) == REQUIRED_KEYS
    assert db.query_one()["program"] is not None
    assert db.query_one()["url"] is not None


@pytest.mark.db
def test_duplicate_rows_do_not_duplicate_database():
    db = FakeDatabase()

    row = {
        "p_id": 1,
        "program": "Computer Science",
        "comments": "Test row",
        "date_added": "2026-05-01",
        "url": "https://example.com/1",
        "status": "Accepted",
        "term": "Fall 2026",
        "us_or_international": "American",
        "gpa": 3.8,
        "gre": 165.0,
        "gre_v": 160.0,
        "gre_aw": 4.5,
        "degree": "Masters",
        "llm_generated_program": "Computer Science",
        "llm_generated_university": "Johns Hopkins University",
    }

    db.insert(row)
    db.insert(row)

    assert db.count() == 1


@pytest.mark.db
def test_query_function_returns_expected_keys():
    result = {
        "Q1 Fall 2026 entries": ["Answer: 1"],
        "Q2 Percentage international students": ["Answer: 23.60%"],
    }

    assert "Q1 Fall 2026 entries" in result
    assert "Q2 Percentage international students" in result