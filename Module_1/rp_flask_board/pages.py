"""Blueprint routes for the personal Flask portfolio website."""

import json
from pathlib import Path

from flask import Blueprint, render_template


pages = Blueprint("pages", __name__)

BASE_DIR = Path(__file__).resolve().parent
PROJECTS_FILE = BASE_DIR / "projects.json"


def load_projects():
    """Load semester portfolio projects from the JSON data file."""

    with PROJECTS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data["projects"]


@pages.route("/")
def home():
    """Render the home page."""

    return render_template(
        "home.html",
        title="Home",
        active_page="home",
    )


@pages.route("/contact")
def contact():
    """Render the contact page."""

    return render_template(
        "contact.html",
        title="Contact",
        active_page="contact",
    )


@pages.route("/projects")
def projects():
    """Render the semester project portfolio."""

    project_list = load_projects()

    return render_template(
        "projects.html",
        title="Projects",
        active_page="projects",
        projects=project_list,
    )