\# Module 2 – GradCafe Data Collection and Standardization



\## Name



Amr Mansour



\## JHED ID



amansou8@jh.edu



\## Assignment



Module 2 – Graduate Admissions Data Collection, Cleaning, and Standardization



\## Repository



jhu\_software\_concepts



\## Approach



This project collects publicly available graduate admissions data from GradCafe and stores it in structured JSON format for future analysis.



\### Scraping Process



The solution was implemented in Python 3 and uses:



\* urllib for URL construction and robots.txt validation

\* Selenium for browser rendering and page navigation

\* BeautifulSoup for HTML parsing

\* JSON for persistent storage



Before scraping, robots.txt was reviewed and verified. Evidence is included as screenshot.jpg.



The scraper:



1\. Checks robots.txt permissions.

2\. Creates GradCafe survey URLs programmatically.

3\. Uses Selenium to retrieve rendered page content.

4\. Parses applicant records using BeautifulSoup and regular expressions.

5\. Extracts admissions information including:



&#x20;  \* Program Name

&#x20;  \* University

&#x20;  \* Applicant Status

&#x20;  \* Comments

&#x20;  \* Date Added

&#x20;  \* Applicant URL

&#x20;  \* Acceptance/Rejection Dates

&#x20;  \* Start Term

&#x20;  \* Degree Type

&#x20;  \* GPA

&#x20;  \* GRE Metrics

&#x20;  \* Applicant Type

6\. Preserves original raw text for reproducibility.

7\. Stores all results in applicant\_data.json.



The scraper collected more than 30,000 applicant records.



\### Data Cleaning



The instructor-provided TinyLlama standardization package was included under:



Module\_2/llm\_hosting



An installation attempt was made using the provided requirements.txt and application files.



The package depended on llama-cpp-python. Installation failed on the local Windows/Python 3.14 environment because the package required native C++ compilation tools that were not available.



As a fallback approach, local canonical matching was implemented using:



\* rapidfuzz

\* canon\_programs.txt

\* canon\_universities.txt



The cleaning process generated:



llm\_extend\_applicant\_data.json



Additional fields were added:



\* standardized\_program\_name

\* standardized\_university



Original values were preserved for traceability.



\## Files



\* scrape.py

\* clean.py

\* applicant\_data.json

\* llm\_extend\_applicant\_data.json

\* requirements.txt

\* screenshot.jpg

\* llm\_hosting/



\## Known Issues



The instructor-provided TinyLlama implementation could not be executed due to a llama-cpp-python build failure on the local environment. The package attempted local compilation and required unavailable C/C++ build tools.



A local canonical matching fallback was implemented to complete the standardization requirement while preserving reproducibility.



\## Execution



Scraping:



python scrape.py



Cleaning:



python clean.py



\## Python Version



Python 3.14



