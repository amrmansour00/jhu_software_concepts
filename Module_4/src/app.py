from flask import Flask, jsonify, render_template, request
from query_data import run_queries


class AppState:
    def __init__(self):
        self.busy = False


def format_results(raw_results):
    formatted = {}

    for question, rows in raw_results.items():
        answers = []

        for row in rows:
            if len(row) == 1:
                value = row[0]
                answers.append(f"Answer: {value}")
            else:
                value = " | ".join(str(item) for item in row)
                answers.append(f"Answer: {value}")

        formatted[question] = answers

    return formatted


def create_app(
    query_function=None,
    loader_function=None,
    state=None
):
    app = Flask(__name__)
    app.config["TESTING"] = False

    app_state = state or AppState()
    query_function = query_function or run_queries

    def default_loader():
        return {"loaded": 0}

    loader_function = loader_function or default_loader

    @app.route("/")
    @app.route("/analysis")
    def analysis():
        raw_results = query_function()
        results = format_results(raw_results)

        return render_template(
            "index.html",
            results=results
        )

    @app.route("/pull-data", methods=["POST"])
    def pull_data():
        if app_state.busy:
            return jsonify({
                "ok": False,
                "busy": True,
                "message": "A data pull is already running."
            }), 409

        app_state.busy = True

        try:
            load_result = loader_function()

            app_state.busy = False

            return jsonify({
                "ok": True,
                "busy": False,
                "message": "Pull Data completed successfully.",
                "result": load_result
            }), 200

        except Exception as error:
            app_state.busy = False

            return jsonify({
                "ok": False,
                "busy": False,
                "message": str(error)
            }), 500

    @app.route("/update-analysis", methods=["POST"])
    def update_analysis():
        if app_state.busy:
            return jsonify({
                "ok": False,
                "busy": True,
                "message": "Analysis cannot update while data pull is running."
            }), 409

        return jsonify({
            "ok": True,
            "busy": False,
            "message": "Analysis updated successfully."
        }), 200

    return app


if __name__ == "__main__":  # pragma: no cover
    flask_app = create_app()
    flask_app.run(debug=True)