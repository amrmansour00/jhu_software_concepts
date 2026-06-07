from flask import Flask, render_template, redirect, url_for, flash
from query_data import run_queries
import subprocess

app = Flask(__name__)
app.secret_key = "module3-secret-key"

scraping_running = False


@app.route("/")
def index():

    raw_results = run_queries()

    results = {}

    for question, rows in raw_results.items():

        cleaned_rows = []

        for row in rows:

            if len(row) == 1:
                cleaned_rows.append(str(row[0]))
            else:
                cleaned_rows.append(
                    " | ".join(str(x) for x in row)
                )

        results[question] = cleaned_rows

    return render_template(
        "index.html",
        results=results
    )


@app.route("/pull-data", methods=["POST"])
def pull_data():

    global scraping_running

    if scraping_running:
        flash(
            "Data pull is already running. Please wait."
        )
        return redirect(url_for("index"))

    scraping_running = True

    try:
        subprocess.Popen(
            ["python", "load_data.py"]
        )

        flash(
            "Pull Data started. Latest GradCafe data is being loaded into PostgreSQL."
        )

    except Exception as error:

        flash(
            f"Could not start Pull Data: {error}"
        )

        scraping_running = False

    return redirect(url_for("index"))


@app.route("/update-analysis", methods=["POST"])
def update_analysis():

    if scraping_running:

        flash(
            "Analysis cannot be refreshed while data pull is running."
        )

        return redirect(url_for("index"))

    flash(
        "Analysis refreshed using the latest database records."
    )

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)