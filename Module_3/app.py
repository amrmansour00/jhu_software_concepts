import subprocess
import sys
import threading
from pathlib import Path

from flask import Flask, flash, redirect, render_template, url_for

from query_data import run_queries


BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
MODULE_2_DIR = REPO_DIR / "Module_2"

app = Flask(__name__)
app.secret_key = "module3-secret-key"

_state_lock = threading.Lock()
scraping_running = False
last_pull_message = None


def format_results(raw_results):
    """Convert database tuples to strings for HTML rendering."""
    results = {}

    for question, rows in raw_results.items():
        cleaned_rows = []

        for row in rows:
            if len(row) == 1:
                cleaned_rows.append(str(row[0]))
            else:
                cleaned_rows.append(
                    " | ".join(
                        "None" if value is None else str(value)
                        for value in row
                    )
                )

        results[question] = cleaned_rows

    return results


def run_command(script_path, cwd):
    """Run one Python pipeline script and fail on errors."""
    print(f"Running: {script_path}")

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )

    if completed.stdout:
        print(completed.stdout)

    if completed.stderr:
        print(completed.stderr)

    if completed.returncode != 0:
        raise RuntimeError(
            f"{script_path.name} failed with "
            f"exit code {completed.returncode}"
        )


def data_pull_worker():
    """
    Run the Module 2 refresh pipeline and then load the
    resulting standardized data incrementally into PostgreSQL.
    """
    global scraping_running
    global last_pull_message

    try:
        # Module 2 scraper is Cloudflare-safe. If live access
        # is blocked it preserves the existing collected dataset.
        run_command(
            MODULE_2_DIR / "scrape.py",
            MODULE_2_DIR,
        )

        run_command(
            MODULE_2_DIR / "repair_applicant_data.py",
            MODULE_2_DIR,
        )

        run_command(
            MODULE_2_DIR / "clean.py",
            MODULE_2_DIR,
        )

        run_command(
            BASE_DIR / "load_data.py",
            BASE_DIR,
        )

        last_pull_message = (
            "Data pull completed successfully. "
            "Module 2 data was refreshed and PostgreSQL "
            "was updated incrementally."
        )

    except Exception as error:
        last_pull_message = (
            f"Data pull failed: {error}"
        )

        print(last_pull_message)

    finally:
        with _state_lock:
            scraping_running = False


@app.route("/")
def index():
    raw_results = run_queries()
    results = format_results(raw_results)

    return render_template(
        "index.html",
        results=results,
        scraping_running=scraping_running,
        last_pull_message=last_pull_message,
    )


@app.route("/pull-data", methods=["POST"])
def pull_data():
    global scraping_running

    with _state_lock:
        if scraping_running:
            flash(
                "Data pull is already running. Please wait."
            )
            return redirect(url_for("index"))

        scraping_running = True

    worker = threading.Thread(
        target=data_pull_worker,
        daemon=True,
    )
    worker.start()

    flash(
        "Data pull started in the background. "
        "Module 2 will refresh the source data and "
        "PostgreSQL will be updated without deleting "
        "existing records."
    )

    return redirect(url_for("index"))


@app.route("/update-analysis", methods=["POST"])
def update_analysis():
    if scraping_running:
        flash(
            "Analysis cannot be refreshed while "
            "the data pull is running."
        )
        return redirect(url_for("index"))

    flash(
        "Analysis refreshed using the latest "
        "PostgreSQL records."
    )

    return redirect(url_for("index"))


@app.route("/pull-status")
def pull_status():
    """Simple status API for the background data pull."""
    return {
        "running": scraping_running,
        "message": last_pull_message,
    }


if __name__ == "__main__":
    # Disable the Flask reloader because it creates a second
    # process and would make in-memory background-task state
    # difficult to interpret during this assignment.
    app.run(
        debug=True,
        use_reloader=False,
    )