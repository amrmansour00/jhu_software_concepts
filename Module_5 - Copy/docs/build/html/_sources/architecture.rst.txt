Architecture
============

The application is organized into web, ETL, database, and testing layers.

Web Layer
---------

The web layer is implemented in ``src/app.py`` using Flask. It provides the
``/analysis`` route and the ``/pull-data`` and ``/update-analysis`` endpoints.

ETL Layer
---------

The ETL layer is implemented in ``src/load_data.py``. It creates the required
applicants table and loads cleaned GradCafe records into PostgreSQL.

Database and Query Layer
------------------------

The query layer is implemented in ``src/query_data.py``. It connects to
PostgreSQL using ``DATABASE_URL`` and returns the analysis results used by
the Flask page.

Testing Layer
-------------

The ``tests`` folder contains Pytest tests for page rendering, button behavior,
analysis formatting, database insertion behavior, and integration flows.