"""Tests for RabbitMQ worker."""

import json
from types import SimpleNamespace

import pytest

import consumer


class FakeConnection:
    """Fake DB connection."""

    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def commit(self):
        """Commit transaction."""
        self.committed = True

    def rollback(self):
        """Rollback transaction."""
        self.rolled_back = True


class FakeChannel:
    """Fake RabbitMQ channel."""

    def __init__(self):
        self.acked = False
        self.nacked = False

    def basic_ack(self, delivery_tag):
        """Acknowledge message."""
        self.acked = delivery_tag

    def basic_nack(self, delivery_tag, requeue=False):
        """Reject message."""
        self.nacked = (delivery_tag, requeue)


@pytest.mark.integration
def test_handle_task_scrape(monkeypatch):
    """Scrape task routes to DB loader."""
    connection = FakeConnection()

    monkeypatch.setenv("SEED_JSON", "/data/applicant_data.json")
    monkeypatch.setattr(consumer, "get_database_connection", lambda: connection)
    monkeypatch.setattr(
        consumer,
        "handle_scrape_new_data",
        lambda _connection, _json, _source: {"inserted": 2},
    )

    result = consumer.handle_task(
        {"kind": "scrape_new_data", "payload": {"source": "test"}}
    )

    assert result == {"inserted": 2}
    assert connection.committed is True


@pytest.mark.integration
def test_handle_task_recompute(monkeypatch):
    """Recompute task routes to analytics."""
    connection = FakeConnection()

    monkeypatch.setattr(consumer, "get_database_connection", lambda: connection)
    monkeypatch.setattr(
        consumer,
        "recompute_analytics",
        lambda _connection: {"applicant_count": 2},
    )

    result = consumer.handle_task({"kind": "recompute_analytics", "payload": {}})

    assert result == {"applicant_count": 2}
    assert connection.committed is True


@pytest.mark.integration
def test_on_message_ack(monkeypatch):
    """Successful message is acknowledged."""
    channel = FakeChannel()
    method = SimpleNamespace(delivery_tag=7)

    monkeypatch.setattr(consumer, "handle_task", lambda _task: {"ok": True})

    consumer.on_message(
        channel,
        method,
        None,
        json.dumps({"kind": "recompute_analytics"}).encode("utf-8"),
    )

    assert channel.acked == 7


@pytest.mark.integration
def test_on_message_nack(monkeypatch):
    """Failed message is rejected without requeue."""
    channel = FakeChannel()
    method = SimpleNamespace(delivery_tag=9)

    def bad_task(_task):
        raise RuntimeError("bad task")

    monkeypatch.setattr(consumer, "handle_task", bad_task)

    consumer.on_message(
        channel,
        method,
        None,
        json.dumps({"kind": "bad"}).encode("utf-8"),
    )

    assert channel.nacked == (9, False)