"""Setup script for the GradCafe analytics project."""

from setuptools import setup

setup(
    name="gradcafe-analytics",
    version="1.0.0",
    description="Software assurance hardening for GradCafe analytics.",
    py_modules=["app", "db", "load_data", "query_data"],
    package_dir={"": "src"},
    install_requires=[
        "Flask",
        "psycopg[binary]",
        "python-dotenv",
    ],
)