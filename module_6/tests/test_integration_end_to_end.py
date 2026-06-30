"""End-to-end tests for pull, update, and render flow."""

import pytest
from bs4 import BeautifulSoup

from app import create_app


class FakeStore:
    """Small in-memory store used as an integration test double."""

    def __init__(self):
        self.rows = {}

    def load(self):
        """Load fake records idempotently."""
        records = [
            {
                "url": "https://example.com/1",
                "status": "Accepted",
                "term": "Fall 2026",
            },
            {
                "url": "https://example.com/2",
                "status": "Rejected",
                "term": "Fall 2026",
            },
        ]

        for record in records:
            self.rows[record["url"]] = record

        return {"loaded": len(records)}

    def analysis(self, limit=10):
        """Return analysis output from fake records."""
        total = min(len(self.rows), limit)
        accepted = sum(
            1 for row in self.rows.values()
            if row["status"] == "Accepted"
        )

        percentage = 0.0
        if total:
            percentage = round((accepted / len(self.rows)) * 100, 2)

        return {
            "Q1 Fall 2026 entries": [(total,)],
            "Q5 Percentage Fall 2026 acceptances": [(f"{percentage:.2f}%",)],
        }


@pytest.mark.integration
def test_end_to_end_pull_update_render():
    """Verify pull, update, and analysis rendering."""
    store = FakeStore()

    app = create_app(
        query_function=store.analysis,
        loader_function=store.load,
    )

    client = app.test_client()

    assert client.post("/pull-data").status_code == 200
    assert client.post("/update-analysis").status_code == 200

    page = client.get("/analysis")
    soup = BeautifulSoup(page.data, "html.parser")
    text = soup.get_text()

    assert page.status_code == 200
    assert "Answer: 2" in text
    assert "Answer: 50.00%" in text


@pytest.mark.integration
def test_multiple_pulls_with_overlap_remain_idempotent():
    """Verify repeated pulls with overlapping data stay unique."""
    store = FakeStore()

    app = create_app(
        query_function=store.analysis,
        loader_function=store.load,
    )

    client = app.test_client()
    client.post("/pull-data")
    client.post("/pull-data")

    assert len(store.rows) == 2