Testing Guide
=============

The project uses Pytest and pytest-cov.

Markers
-------

All tests are marked using one or more of the following markers:

- ``web``
- ``buttons``
- ``analysis``
- ``db``
- ``integration``

Run Tests
---------

.. code-block:: bash

   pytest -m "web or buttons or analysis or db or integration"

Coverage
--------

The test suite is configured to reach 100% coverage for the Flask application.

Selectors
---------

The HTML page includes stable selectors for UI tests:

- ``data-testid="pull-data-btn"``
- ``data-testid="update-analysis-btn"``

Test Doubles
------------

The tests use fake query functions, fake loaders, and fake stores so the
test suite does not depend on live internet scraping or long-running jobs.