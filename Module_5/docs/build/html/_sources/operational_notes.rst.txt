Operational Notes
=================

Busy-State Policy
-----------------

The application uses a simple busy-state object. When a pull operation is in
progress, additional pull requests and analysis update requests return a busy
response.

Idempotency Strategy
--------------------

The tests use URL-based uniqueness to prevent duplicate records from being
created when overlapping data is pulled more than once.

Troubleshooting
---------------

If the application cannot connect to PostgreSQL, verify that ``DATABASE_URL``
is set correctly in the local ``.env`` file.

If tests fail in GitHub Actions, confirm that dependencies are listed in
``requirements.txt`` and that all tests are properly marked.