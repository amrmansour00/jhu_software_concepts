"""Flask web service for Module 6."""

import os

import psycopg
from flask import Flask, jsonify, render_template

from publisher import publish_task
from query_data import format_results, run_queries


app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static",
)


def get_connection():
    """Create database connection from DATABASE_URL."""
    return psycopg.connect(os.environ["DATABASE_URL"])


@app.get("/")
@app.get("/analysis")
def analysis():
    """Render current analytics from PostgreSQL."""
    with get_connection() as connection:
        raw_results = run_queries(connection)
    return render_template("index.html", results=format_results(raw_results))


@app.post("/pull-data")
def pull_data():
    """Queue scrape/load task and return immediately."""
    try:
        publish_task("scrape_new_data", payload={})
    except Exception as error:  # pylint: disable=broad-exception-caught
        app.logger.exception("Failed to publish scrape_new_data")
        return jsonify({"error": "publish_failed", "detail": str(error)}), 503

    return jsonify({"status": "queued", "task": "scrape_new_data"}), 202


@app.post("/update-analysis")
def update_analysis():
    """Queue analytics recompute task and return immediately."""
    try:
        publish_task("recompute_analytics", payload={})
    except Exception as error:  # pylint: disable=broad-exception-caught
        app.logger.exception("Failed to publish recompute_analytics")
        return jsonify({"error": "publish_failed", "detail": str(error)}), 503

    return jsonify({"status": "queued", "task": "recompute_analytics"}), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
