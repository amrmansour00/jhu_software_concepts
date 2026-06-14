\# Module 4 – Testing and Continuous Integration



\## Overview



This project extends the GradCafe PostgreSQL analysis application by adding automated testing, continuous integration, and quality assurance practices.



\## Components



\* Flask web application

\* PostgreSQL data analysis

\* Pytest automated test suite

\* GitHub Actions workflow

\* Coverage reporting



\## Running the Application



```bash

python src/app.py

```



Open:



http://127.0.0.1:5000



\## Running Tests



```bash

pytest -m "web or buttons or analysis or db or integration"

```



Current Result:



\* 17 tests passed

\* 100% coverage



\## GitHub Actions



Tests run automatically on every push to the main branch.



\## Files



\* src/app.py

\* src/load\_data.py

\* src/query\_data.py

\* tests/

\* actions\_success.png

\* coverage\_summary.txt



