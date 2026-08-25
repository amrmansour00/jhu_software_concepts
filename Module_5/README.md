# GradCafe Analytics - Module 5

## Project Overview

This project extends the GradCafe Analytics application with software assurance, dependency management, database security, automated testing, documentation, and continuous integration practices.

The application uses Flask and PostgreSQL to load and analyze graduate admissions data while applying secure configuration and software engineering practices.

## Features

- Flask web application
- PostgreSQL database integration
- Environment-based database configuration
- SSL-enabled PostgreSQL connections
- Parameterized SQL queries
- Input validation and query limit controls
- Automated data loading and analytics
- Pytest unit, integration, database, and security tests
- 100% source-code test coverage
- Pylint code quality validation
- Sphinx documentation
- Read the Docs integration
- GitHub Actions continuous integration
- Dependency analysis
- Snyk dependency vulnerability scanning

## Project Structure

```text
Module_5/
|-- docs/
|-- src/
|   |-- app.py
|   |-- db.py
|   |-- load_data.py
|   `-- query_data.py
|-- tests/
|-- README.md
|-- requirements.txt
|-- setup.py
|-- pytest.ini
|-- .env.example
|-- .readthedocs.yaml
|-- dependency.svg
|-- coverage_summary.txt
|-- pylint_score.txt
|-- snyk-analysis.png
`-- ci_success.png