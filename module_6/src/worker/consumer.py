"""RabbitMQ worker consumer for Module 6."""

import json
import os
import sys
from pathlib import Path

import pika
import psycopg

sys.path.append(str(Path(__file__).resolve().parents[1]))

from db.load_data import (  # pylint: disable=wrong-import-position
    handle_scrape_new_data,
    recompute_analytics,
)


EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "tasks"


def get_database_connection():
    """Create database connection from DATABASE_URL."""
    return psycopg.connect(os.environ["DATABASE_URL"])


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
    channel.basic_qos(prefetch_count=1)

    return connection, channel


def handle_task(task):
    """Route task message to the correct handler."""
    kind = task.get("kind")
    payload = task.get("payload", {})

    with get_database_connection() as connection:
        try:
            if kind == "scrape_new_data":
                result = handle_scrape_new_data(
                    connection,
                    os.environ["SEED_JSON"],
                    payload.get("source", "gradcafe_seed"),
                )
            elif kind == "recompute_analytics":
                result = recompute_analytics(connection)
            else:
                raise ValueError(f"Unknown task kind: {kind}")

            connection.commit()
            return result
        except Exception:
            connection.rollback()
            raise


def on_message(channel, method, _properties, body):
    """Process one RabbitMQ message and acknowledge after commit."""
    try:
        task = json.loads(body.decode("utf-8"))
        handle_task(task)
        channel.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:  # pylint: disable=broad-exception-caught
        channel.basic_nack(
            delivery_tag=method.delivery_tag,
            requeue=False,
        )


def main():
    """Start long-running RabbitMQ worker."""
    connection, channel = open_channel()
    channel.basic_consume(queue=QUEUE, on_message_callback=on_message)

    try:
        channel.start_consuming()
    finally:
        connection.close()


if __name__ == "__main__":
    main()