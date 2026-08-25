"""Package configuration for the Module 6 GradCafe microservices application."""

from setuptools import setup

setup(
    name="gradcafe-microservices",
    version="1.0.0",
    description=(
        "Containerized GradCafe analytics application using Flask, "
        "PostgreSQL, RabbitMQ, and a background worker."
    ),
    py_modules=[
        "publisher",
        "query_data",
        "run",
        "consumer",
    ],
    package_dir={
        "": "src",
        "web": "src/web",
        "worker": "src/worker",
    },
    install_requires=[
        "Flask",
        "psycopg[binary]",
        "python-dotenv",
        "pika",
    ],
)