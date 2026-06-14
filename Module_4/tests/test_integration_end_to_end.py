import pytest
from bs4 import BeautifulSoup
from app import create_app


class FakeStore:
    def __init__(self):
        self.rows = {}

    def load(self):
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

    def analysis(self):
        total = len(self.rows)
        accepted = sum(
            1 for row in self.rows.values()
            if row["status"] == "Accepted"
        )

        percentage = 0.0

        if total:
            percentage = round((accepted / total) * 100, 2)

        return {
            "Q1 Fall 2026 entries": [(total,)],
            "Q5 Percentage Fall 2026 acceptances": [(f"{percentage:.2f}%",)],
        }


@pytest.mark.integration
def test_end_to_end_pull_update_render():
    store = FakeStore()

    app = create_app(
        query_function=store.analysis,
        loader_function=store.load
    )

    client = app.test_client()

    pull_response = client.post("/pull-data")
    assert pull_response.status_code == 200
    assert pull_response.json["ok"] is True

    update_response = client.post("/update-analysis")
    assert update_response.status_code == 200
    assert update_response.json["ok"] is True

    page = client.get("/analysis")
    assert page.status_code == 200

    soup = BeautifulSoup(page.data, "html.parser")
    text = soup.get_text()

    assert "Answer: 2" in text
    assert "Answer: 50.00%" in text


@pytest.mark.integration
def test_multiple_pulls_with_overlap_do_not_duplicate():
    store = FakeStore()

    app = create_app(
        query_function=store.analysis,
        loader_function=store.load
    )

    client = app.test_client()

    client.post("/pull-data")
    client.post("/pull-data")

    assert len(store.rows) == 2