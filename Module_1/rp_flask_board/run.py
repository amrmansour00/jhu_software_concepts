"""Application entry point for the Flask portfolio website."""

from flask import Flask

from pages import pages


def create_app():
    """Create and configure the Flask application."""

    app = Flask(__name__)

    app.register_blueprint(pages)

    return app


if __name__ == "__main__":
    flask_app = create_app()

    flask_app.run(
        host="0.0.0.0",
        port=8080,
        debug=False,
    )