"""Tests for Module 6 RabbitMQ publisher and worker."""

import json
from types import SimpleNamespace

import pika
import pytest

import consumer
import publisher


class FakeDBConnection:
    """Fake database connection."""

    def __init__(self):
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class FakeChannel:
    """Fake RabbitMQ channel."""

    def __init__(self):
        self.acked = False
        self.nacked = False
        self.published = None
        self.exchange = None
        self.queue = None
        self.binding = None
        self.prefetch = None
        self.consume_args = None
        self.consumed = False

    def exchange_declare(self, **kwargs):
        self.exchange = kwargs

    def queue_declare(self, **kwargs):
        self.queue = kwargs

    def queue_bind(self, **kwargs):
        self.binding = kwargs

    def basic_qos(self, **kwargs):
        self.prefetch = kwargs

    def basic_publish(self, **kwargs):
        self.published = kwargs

    def basic_ack(self, delivery_tag):
        self.acked = delivery_tag

    def basic_nack(self, delivery_tag, requeue=False):
        self.nacked = (delivery_tag, requeue)

    def basic_consume(self, **kwargs):
        self.consume_args = kwargs

    def start_consuming(self):
        self.consumed = True


class FakeRabbitConnection:
    """Fake RabbitMQ connection."""

    def __init__(self, channel=None):
        self.fake_channel = channel or FakeChannel()
        self.closed = False

    def channel(self):
        return self.fake_channel

    def close(self):
        self.closed = True


@pytest.mark.integration
def test_publisher_open_channel(monkeypatch):
    """Publisher declares durable RabbitMQ entities."""
    channel = FakeChannel()
    connection = FakeRabbitConnection(channel)

    monkeypatch.setenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@localhost:5672/",
    )
    monkeypatch.setattr(
        publisher.pika,
        "BlockingConnection",
        lambda _params: connection,
    )

    returned_connection, returned_channel = publisher.open_channel()

    assert returned_connection is connection
    assert returned_channel is channel
    assert channel.exchange["exchange"] == publisher.EXCHANGE
    assert channel.exchange["durable"] is True
    assert channel.queue["queue"] == publisher.QUEUE
    assert channel.queue["durable"] is True
    assert channel.binding["routing_key"] == publisher.ROUTING_KEY


@pytest.mark.integration
def test_publish_task(monkeypatch):
    """Publisher sends persistent JSON and closes connection."""
    channel = FakeChannel()
    connection = FakeRabbitConnection(channel)

    monkeypatch.setattr(
        publisher,
        "open_channel",
        lambda: (connection, channel),
    )

    publisher.publish_task(
        "scrape_new_data",
        payload={"source": "test"},
        headers={"request-id": "123"},
    )

    assert channel.published is not None

    body = json.loads(channel.published["body"].decode("utf-8"))

    assert body["kind"] == "scrape_new_data"
    assert body["payload"] == {"source": "test"}
    assert "ts" in body

    properties = channel.published["properties"]

    assert properties.delivery_mode == 2
    assert properties.headers == {"request-id": "123"}
    assert connection.closed is True


@pytest.mark.integration
def test_publish_task_defaults(monkeypatch):
    """Publisher supplies empty payload and headers by default."""
    channel = FakeChannel()
    connection = FakeRabbitConnection(channel)

    monkeypatch.setattr(
        publisher,
        "open_channel",
        lambda: (connection, channel),
    )

    publisher.publish_task("recompute_analytics")

    body = json.loads(channel.published["body"].decode("utf-8"))

    assert body["payload"] == {}
    assert channel.published["properties"].headers == {}


@pytest.mark.integration
def test_handle_task_scrape(monkeypatch):
    """Scrape task routes to database loader."""
    connection = FakeDBConnection()

    monkeypatch.setenv("SEED_JSON", "/data/applicant_data.json")
    monkeypatch.setattr(
        consumer,
        "get_database_connection",
        lambda: connection,
    )
    monkeypatch.setattr(
        consumer,
        "handle_scrape_new_data",
        lambda _connection, _json, _source: {"inserted": 2},
    )

    result = consumer.handle_task(
        {
            "kind": "scrape_new_data",
            "payload": {"source": "test"},
        }
    )

    assert result == {"inserted": 2}
    assert connection.committed is True


@pytest.mark.integration
def test_handle_task_recompute(monkeypatch):
    """Recompute task routes to analytics."""
    connection = FakeDBConnection()

    monkeypatch.setattr(
        consumer,
        "get_database_connection",
        lambda: connection,
    )
    monkeypatch.setattr(
        consumer,
        "recompute_analytics",
        lambda _connection: {"applicant_count": 2},
    )

    result = consumer.handle_task(
        {"kind": "recompute_analytics", "payload": {}}
    )

    assert result == {"applicant_count": 2}
    assert connection.committed is True


@pytest.mark.integration
def test_handle_task_unknown_rolls_back(monkeypatch):
    """Unknown tasks roll back their transaction."""
    connection = FakeDBConnection()

    monkeypatch.setattr(
        consumer,
        "get_database_connection",
        lambda: connection,
    )

    with pytest.raises(ValueError, match="Unknown task kind"):
        consumer.handle_task(
            {"kind": "not-a-real-task", "payload": {}}
        )

    assert connection.rolled_back is True
    assert connection.committed is False


@pytest.mark.integration
def test_on_message_ack(monkeypatch):
    """Successful message is acknowledged."""
    channel = FakeChannel()
    method = SimpleNamespace(delivery_tag=7)

    monkeypatch.setattr(
        consumer,
        "handle_task",
        lambda _task: {"ok": True},
    )

    consumer.on_message(
        channel,
        method,
        None,
        json.dumps(
            {"kind": "recompute_analytics"}
        ).encode("utf-8"),
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


@pytest.mark.integration
def test_worker_open_channel_success(monkeypatch):
    """Worker configures RabbitMQ channel on successful connection."""
    channel = FakeChannel()
    connection = FakeRabbitConnection(channel)

    monkeypatch.setenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@localhost:5672/",
    )
    monkeypatch.setattr(
        consumer.pika,
        "BlockingConnection",
        lambda _params: connection,
    )

    returned_connection, returned_channel = consumer.open_channel()

    assert returned_connection is connection
    assert returned_channel is channel
    assert channel.prefetch == {"prefetch_count": 1}


@pytest.mark.integration
def test_worker_open_channel_retries(monkeypatch):
    """Worker retries after a temporary RabbitMQ connection failure."""
    channel = FakeChannel()
    connection = FakeRabbitConnection(channel)
    calls = {"count": 0}

    monkeypatch.setenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@localhost:5672/",
    )

    def connect(_params):
        calls["count"] += 1

        if calls["count"] == 1:
            raise pika.exceptions.AMQPConnectionError("not ready")

        return connection

    monkeypatch.setattr(
        consumer.pika,
        "BlockingConnection",
        connect,
    )
    monkeypatch.setattr(consumer.time, "sleep", lambda _seconds: None)

    returned_connection, _ = consumer.open_channel()

    assert returned_connection is connection
    assert calls["count"] == 2


@pytest.mark.integration
def test_worker_open_channel_exhausts_retries(monkeypatch):
    """Worker raises after all RabbitMQ connection attempts fail."""
    monkeypatch.setenv(
        "RABBITMQ_URL",
        "amqp://guest:guest@localhost:5672/",
    )

    def always_fail(_params):
        raise pika.exceptions.AMQPConnectionError("not ready")

    monkeypatch.setattr(
        consumer.pika,
        "BlockingConnection",
        always_fail,
    )
    monkeypatch.setattr(consumer.time, "sleep", lambda _seconds: None)

    with pytest.raises(
        RuntimeError,
        match="Could not connect to RabbitMQ",
    ):
        consumer.open_channel()


@pytest.mark.integration
def test_worker_main(monkeypatch):
    """Worker consumes tasks and closes RabbitMQ connection."""
    channel = FakeChannel()
    connection = FakeRabbitConnection(channel)

    monkeypatch.setattr(
        consumer,
        "open_channel",
        lambda: (connection, channel),
    )

    consumer.main()

    assert channel.consume_args["queue"] == consumer.QUEUE
    assert channel.consume_args["on_message_callback"] == consumer.on_message
    assert channel.consumed is True
    assert connection.closed is True