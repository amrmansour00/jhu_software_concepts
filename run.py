
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html", title="Home", active_page="home")

@app.route("/contact")
def contact():
    return render_template("contact.html", title="Contact", active_page="contact")

@app.route("/projects")
def projects():
    return render_template("projects.html", title="Projects", active_page="projects")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
