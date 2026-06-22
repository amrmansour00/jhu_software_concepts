Overview and Setup
==================

The GradCafe Analytics application is a Flask-based application that displays
analysis results from GradCafe admissions data stored in PostgreSQL.

Environment Variables
---------------------

The application uses the following environment variable:

``DATABASE_URL``

This variable stores the PostgreSQL connection string.

Run the Application
-------------------

From the ``Module_4`` folder, run:

.. code-block:: bash

   python src/app.py

Open the application at:

.. code-block:: text

   http://127.0.0.1:5000/analysis

Run Tests
---------

Run all marked tests with:

.. code-block:: bash

   pytest -m "web or buttons or analysis or db or integration"