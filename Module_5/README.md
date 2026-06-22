# \# GradCafe Analytics – Module 5

# 

# \## Project Overview

# 

# GradCafe Analytics is a Flask-based web application that loads graduate admission data into a PostgreSQL database and provides interactive analytics through a web interface. The project demonstrates secure database integration, automated testing, documentation, dependency analysis, and continuous integration following software engineering best practices.

# 

# \## Features

# 

# \* Flask web application

# \* PostgreSQL database integration

# \* Automated data loading

# \* Graduate admissions analytics

# \* Pytest unit, integration, and database tests

# \* 100% code coverage

# \* Pylint code quality score of 10/10

# \* Sphinx documentation with Read the Docs

# \* GitHub Actions Continuous Integration

# \* Snyk dependency vulnerability scanning

# 

# \## Project Structure

# 

# ```

# Module\_5/

# ├── docs/

# ├── src/

# ├── tests/

# ├── README.md

# ├── requirements.txt

# ├── setup.py

# ├── pytest.ini

# ├── .env.example

# ├── .readthedocs.yaml

# ├── dependency.svg

# ├── coverage\_summary.txt

# ├── pylint\_score.txt

# ├── snyk-analysis.png

# ├── ci\_success.png

# ```

# 

# \## Installation

# 

# Install the required packages:

# 

# ```bash

# pip install -r requirements.txt

# ```

# 

# \## Environment Variables

# 

# Create a `.env` file using `.env.example` and configure:

# 

# ```text

# DATABASE\_URL=postgresql://username:password@localhost:5432/gradcafe

# ```

# 

# \## Running the Application

# 

# ```bash

# python src/app.py

# ```

# 

# The application starts a local Flask server where users can load GradCafe data and generate analytics.

# 

# \## Running the Tests

# 

# ```bash

# pytest -m "web or buttons or analysis or db or integration"

# ```

# 

# The project includes:

# 

# \* Web interface tests

# \* Button/action tests

# \* Database tests

# \* Analysis formatting tests

# \* End-to-end integration tests

# 

# Current test status:

# 

# \* 28 tests passed

# \* 100% code coverage

# 

# \## Code Quality

# 

# Run:

# 

# ```bash

# pylint src --fail-under=10

# ```

# 

# Final score:

# 

# \* \*\*10.00/10\*\*

# 

# \## Documentation

# 

# Project documentation is published using Sphinx and Read the Docs.

# 

# Read the Docs:

# 

# \*\*Replace this line with your actual Read the Docs URL.\*\*

# 

# \## Dependency Graph

# 

# The project dependency graph is included in:

# 

# \* `dependency.svg`

# 

# \## Security Scan

# 

# Dependency vulnerability scanning was completed successfully using Snyk Open Source.

# 

# Evidence:

# 

# \* `snyk-analysis.png`

# 

# \## Continuous Integration

# 

# GitHub Actions automatically validates the project after every push.

# 

# Evidence:

# 

# \* `ci\_success.png`

# 

# \## License

# 

# This project was developed for the Johns Hopkins University Modern Software Concepts course and is intended for educational purposes.



