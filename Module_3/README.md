\# Module 3 – GradCafe SQL Analysis



\## Overview



This project loads cleaned GradCafe admissions data from Module 2 into a PostgreSQL database using psycopg. SQL queries are used to analyze applicant records and answer a series of admissions-related questions. The results are displayed dynamically through a Flask web application.



\## Project Structure



\* `load\_data.py` – Creates the applicants table and loads the cleaned GradCafe dataset into PostgreSQL.

\* `query\_data.py` – Executes SQL queries and displays analysis results.

\* `app.py` – Flask application used to display analysis results through a web interface.

\* `templates/index.html` – Main webpage template.

\* `static/style.css` – CSS styling for the webpage.

\* `requirements.txt` – Python dependencies required to run the project.

\* `limitations.pdf` – Discussion of limitations associated with anonymous self-reported admissions data.

\* `screenshots/` – Screenshots of database loading, query output, and webpage results.



\## Database Setup



1\. Create a PostgreSQL database.

2\. Create a `.env` file in the Module\_3 directory containing:



DATABASE\_URL=your\_connection\_string



\## Load Data into PostgreSQL



Run:



python load\_data.py



This script:



\* Connects to PostgreSQL.

\* Creates the applicants table.

\* Loads the cleaned GradCafe dataset from Module 2.

\* Inserts all applicant records into the database.



\## Execute SQL Queries



Run:



python query\_data.py



This script executes all required assignment queries and prints the results to the console.



\## Run the Flask Application



Run:



python app.py



Open the application in a browser:



http://127.0.0.1:5000



The webpage displays query results dynamically and includes:



\* Pull Data button

\* Update Analysis button



\## Screenshots



Screenshots demonstrating successful execution are stored in the `screenshots` folder.



\## Dependencies



Install required packages using:



pip install -r requirements.txt



