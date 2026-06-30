"""RabbitMQ publisher for Flask web service."""

import json
import os
from datetime import datetime, UTC

import pika


EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"


def open_channel():
    """Open RabbitMQ connection and declare durable AMQP entities."""
    rabbitmq_url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()

    channel.exchange_declare(
        exchange=EXCHANGE,
        exchange_type="direct",
        durable=True,
    )
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(
        exchange=EXCHANGE,
        queue=QUEUE,
        routing_key=ROUTING_KEY,
    )

    return connection, channel


def publish_task(kind, payload=None, headers=None):
    """Publish a persistent compact JSON task message."""
    body = json.dumps(
        {
            "kind": kind,
            "ts": datetime.now(UTC).isoformat(),
            "payload": payload or {},
        },
        separators=(",", ":"),
    ).encode("utf-8")

    connection, channel = open_channel()

    try:
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=ROUTING_KEY,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,
                headers=headers or {},
            ),
            mandatory=False,
        )
    finally:
        connection.close()