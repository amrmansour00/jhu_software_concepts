# Module 4 - Testing, Continuous Integration, and Documentation

## EN.605.256.81.SU26 - Modern Software Concepts in Python

## Overview

Module 4 extends the GradCafe PostgreSQL analytics application by adding automated testing, code coverage, continuous integration, and Sphinx documentation.

The project validates the Flask application, PostgreSQL loading logic, SQL analytics, button behavior, formatting, and end-to-end application flows.

The current test suite contains **41 automated tests** and measures coverage across the complete production code under `src`.

---

## Project Structure

```text
Module_4/
|
|-- src/
|   |-- app.py
|   |-- load_data.py
|   |-- query_data.py
|   |-- templates/
|   `-- static/
|
|-- tests/
|   |-- conftest.py
|   |-- test_analysis_format.py
|   |-- test_buttons.py
|   |-- test_db_insert.py
|   |-- test_flask_page.py
|   |-- test_integration_end_to_end.py
|   |-- test_load_data.py
|   `-- test_query_data.py
|
|-- docs/
|   |-- source/
|   `-- build/
|
|-- pytest.ini
|-- requirements.txt
|-- coverage_summary.txt
|-- .readthedocs.yaml
`-- README.md
```

---

## Application Components

### `src/app.py`

Provides the Flask web interface and application routes.

The application supports:

- Main analysis page
- Pull Data behavior
- Update Analysis behavior
- Query-result formatting
- Dependency injection for deterministic testing

### `src/load_data.py`

Loads the repaired and standardized Module 2 applicant dataset into PostgreSQL.

The loader:

- Reads `Module_2/llm_extend_applicant_data.json`
- Validates GPA and GRE-related values
- Creates the PostgreSQL applicants table if needed
- Uses applicant URLs as unique de-duplication keys
- Updates existing applicant records instead of creating duplicates
- Reports data-quality and uniqueness validation statistics

The validated dataset currently contains:

```text
Records processed: 14,805
Database records: 14,805
Unique URLs: 14,805
Invalid GRE totals remaining: 0
Invalid GRE Verbal values remaining: 0
Invalid GRE AW values remaining: 0
Duplicate URL validation: PASSED
```

### `src/query_data.py`

Executes eleven SQL analytics queries against PostgreSQL, including:

- Fall 2026 applicant counts
- International-student percentage
- Average GPA and GRE values
- Acceptance-rate analysis
- Johns Hopkins Computer Science analysis
- Comparison of raw and standardized fields
- Top universities by reported acceptances
- Average GPA by degree type

---

## Running the Application

From the Module 4 directory:

```powershell
python src/app.py
```

Then open:

```text
http://127.0.0.1:5000
```

---

## Running the Tests

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run the complete suite:

```powershell
pytest -v
```

Current result:

```text
41 passed
```

---

## Coverage

Coverage is measured across the complete production source directory:

```text
--cov=src
```

Current result:

```text
Name                Stmts   Miss  Cover
-------------------------------------------------
src/app.py             49      0   100%
src/load_data.py      135      1    99%
src/query_data.py      32      2    94%
-------------------------------------------------
TOTAL                 216      3    99%

Total coverage: 98.61%
```

This is intentionally measured across all production modules rather than only the Flask application.

The remaining uncovered lines are command-line entry-point statements rather than core application logic.

---

## Test Organization

The test suite is organized into several categories.

### Web Tests

Validate Flask pages and response behavior.

### Button Tests

Validate Pull Data and Update Analysis behavior.

### Analysis Tests

Validate result formatting and percentage rendering.

### Database Tests

Validate:

- Numeric cleaning
- Date parsing
- GPA and GRE validation
- Module 2 record mapping
- PostgreSQL table creation
- URL-based de-duplication logic
- Database statistics
- Loader orchestration

### Query Tests

Validate:

- Presence of all eleven SQL questions
- SQL execution behavior
- Query result dictionaries
- Required database configuration
- Console result formatting

### Integration Tests

Validate application workflows through the Flask test client.

External infrastructure is mocked or injected where appropriate so that automated tests remain deterministic and do not depend on network availability or modify the live PostgreSQL database.

The production PostgreSQL workflow was also validated separately against the configured database.

---

## Pytest Markers

The following markers are configured:

```text
web
buttons
analysis
db
integration
```

Examples:

```powershell
pytest -m web
pytest -m db
pytest -m integration
```

Run selected categories:

```powershell
pytest -m "web or buttons or analysis or db or integration"
```

---

## Continuous Integration

GitHub Actions runs automated testing when changes are pushed to the repository.

The CI workflow validates that application behavior and tests continue to pass after code changes.

Supporting GitHub Actions evidence is included in the project files.

---

## Sphinx Documentation

Sphinx documentation is maintained under:

```text
docs/source/
```

The configuration enables:

```text
sphinx.ext.autodoc
sphinx.ext.napoleon
```

The API documentation includes:

- Flask application
- Data-loading functions
- SQL query functions

Build the documentation locally with:

```powershell
docs\make.bat clean
docs\make.bat html
```

The current documentation build completes successfully.

Generated HTML is written to:

```text
docs/build/html/
```

---

## Read the Docs

The project documentation is published through Read the Docs.

The correct project URL is:

```text
https://jhu-software-concepts-amr.readthedocs.io/en/latest/
```

---

## Environment Configuration

The PostgreSQL connection string is stored in:

```text
.env
```

Example:

```text
DATABASE_URL=your_postgresql_connection_string
```

The `.env` file is excluded from version control.

---

## Reproducibility

A clean environment can be prepared using:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then run:

```powershell
pytest -v
```

No local virtual environment, cache directory, credential file, or `.coverage` database should be committed to the repository.

---

## Current Quality Status

```text
Automated tests: 41 passed
Full-source coverage: 98.61%
Flask app coverage: 100%
Loader coverage: 99%
Query coverage: 94%
Sphinx documentation build: successful
PostgreSQL loader validation: passed
Duplicate URL validation: passed
```

---

## Summary

Module 4 demonstrates a complete software-quality workflow around the GradCafe analytics application.

The project combines:

- Automated unit testing
- Flask route testing
- Database-loader testing
- SQL-query testing
- Integration testing
- Full-source coverage measurement
- Continuous integration
- Sphinx API documentation
- Reproducible environment configuration

The revised test suite measures the complete application codebase rather than only the Flask module and provides substantially stronger validation of the database and analytics logic.