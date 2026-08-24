# Module 2 - GradCafe Data Collection, Repair, and Standardization



## EN.605.256.81.SU26 - Modern Software Concepts in Python



This project implements a reproducible data-processing workflow for graduate admissions data collected from GradCafe.



The Module 2 workflow covers:



1. Web data collection

2. Applicant-record parsing

3. Data validation and repair

4. Program and university standardization

5. Canonical-list matching

6. Conservative post-processing

7. JSON persistence

8. Validation of the resulting dataset



The project was also revised following grading feedback to correct an issue in the original scraped dataset where some applicant listings had been represented as separate fragments rather than a single applicant record.



---



## Project Structure



```text

Module_2/

|
|-- scrape.py
|-- repair_applicant_data.py
|-- clean.py
|-- applicant_data.json
|-- applicant_data_repaired.json
|-- llm_extend_applicant_data.json
|-- requirements.txt
|-- README.md
|-- www.gradcafe.com.png
|
|-- llm_hosting/
    |-- app.py
    |-- canon_programs.txt
    |-- canon_universities.txt
    |-- requirements.txt
    |-- sample_data.json
    |-- README.md

```



---



# 1. Environment Setup



A Python virtual environment is recommended but should not be committed to the GitHub repository.



Create a virtual environment:



```powershell

python -m venv venv

```



Activate it on Windows:



```powershell

.\\venv\\Scripts\\Activate.ps1

```



Install the required packages:



```powershell

pip install -r requirements.txt

```



The project requirements include:



```text

beautifulsoup4

selenium

lxml

urllib3

requests

rapidfuzz

tqdm

```



The virtual environment itself is intentionally excluded from version control. The `requirements.txt` file provides the dependencies required to reproduce the environment.



---



# 2. Data Collection



The primary scraper is:



```text

scrape.py

```



The scraper is designed to collect graduate admissions results from GradCafe and extract applicant-related information such as:



- Program name

- University

- Applicant status

- Decision date

- Date added

- Degree

- Start term

- Student type

- GPA

- GRE

- GRE Verbal

- GRE Analytical Writing

- Comments

- Entry URL

- Source page



The scraper also checks `robots.txt` before attempting automated access.



---



# 3. Safe Handling of Anti-Bot Protection



During final validation of the project, GradCafe returned a Cloudflare anti-bot challenge instead of the normal admissions-results page.



The scraper was therefore hardened to detect challenge pages before attempting to parse them.



Examples of challenge indicators checked by `scrape.py` include:



```text

cf_chl_opt

cf-chl

Cloudflare

Performance and Security by Cloudflare

Verify you are human

Checking your browser

Attention required

challenge-platform

Just a moment

```



When a challenge page is detected, the scraper:



1. Stops the live scraping operation.

2. Does not interpret the challenge HTML as applicant data.

3. Does not overwrite the existing `applicant_data.json`.

4. Reports the condition clearly in the terminal.



This behavior is intentional. It prevents a temporary website-access restriction from corrupting an already collected dataset.



No attempt is made to bypass Cloudflare or other website access controls.



---



# 4. Original Parsing Issue



Validation of the original dataset identified an important structural issue.



Some GradCafe applicant listings had been captured as two consecutive records.



For example, one record could contain:



```text

Stockholm University Environmental Economics PhD May 31, 2026

Accepted on May 31 Total comments

```



while the following fragment contained:



```text

Accepted on May 31 Fall 2026 International

```



These two fragments represented one applicant submission but had originally been stored as separate records.



This caused unreliable values in fields such as:



```text

program_name

university

date_added

degree

start_term

student_type

gpa

```



For example, decision information such as:



```text

Accepted on May 31 Fall 2026 International

```



could incorrectly appear as a program or university name.



The problem was corrected through a dedicated repair stage rather than silently modifying the original source artifact.



---



# 5. Dataset Repair



The repair workflow is implemented in:



```text

repair_applicant_data.py

```



The script reads the original collected dataset and reconstructs applicant records by combining the primary listing with its associated detail fragment where appropriate.



The original dataset is preserved as:



```text

applicant_data.json

```



The repaired dataset is written separately as:



```text

applicant_data_repaired.json

```



This preserves traceability between the originally collected data and the corrected representation.



---



# 6. Repair Validation



The repaired dataset contains:



```text

Repaired applicant records: 14,805

Missing program names: 4

Missing universities: 0

Missing degrees: 17

Missing applicant status: 0

Missing start term: 1

Duplicate entry URLs: 0

Suspicious program names containing decision text: 0

```



The repair process therefore reduced the malformed 30,000-row representation to **14,805 reconstructed applicant records**.



The reduction is expected because many rows in the original file were fragments belonging to the preceding applicant record rather than independent applicants.



The repair process also checks for duplicate result URLs and suspicious decision text appearing in program names.



---



# 7. Example Repaired Record



A repaired record can contain information such as:



```text

University: Stockholm University

Program: Environmental Economics

Degree: PhD

Status: Accepted

Date added: May 31, 2026

Term: Fall 2026

Student type: International

Entry URL: https://www.thegradcafe.com/result/1020288

```



Another example:



```text

University: Meharry Medical College

Program: Global Health

Degree: PhD

Status: Accepted

Date added: May 30, 2026

Term: Fall 2026

Student type: American

GPA: 3.90

Entry URL: https://www.thegradcafe.com/result/1020287

```



These examples demonstrate that university/program information and applicant-specific decision details are now associated with the same applicant record.



---



# 8. Data Standardization



The next stage is implemented in:



```text

clean.py

```



The cleaning workflow reads:



```text

applicant_data_repaired.json

```



and writes:



```text

llm_extend_applicant_data.json

```



The objective is to standardize naming inconsistencies without changing the semantic meaning of the original data.



---



# 9. Canonical Lists



Canonical program and university names are maintained separately in:



```text

llm_hosting/canon_programs.txt

llm_hosting/canon_universities.txt

```



These files provide reference values for standardization.



Separating canonical values from the processing logic makes the standardization rules easier to inspect, maintain, and extend.



The canonical lists are not treated as permission to replace every similar value with the nearest available name. Matching is deliberately conservative.



---



# 10. Deterministic Post-Processing



`clean.py` contains explicit post-processing rules for known spelling variations and abbreviations.



Examples of university normalization rules include variants such as:



```text

U of T -> University of Toronto

UBC -> University of British Columbia

McGill -> McGill University

```



Explicit corrections are applied before fuzzy matching.



The purpose of these mappings is to correct known representation differences rather than infer a different institution or program.



Changes to these rules are maintained directly in the documented dictionaries in `clean.py`.



---



# 11. Conservative Program Standardization



Program names require particularly careful handling because two similar names may describe genuinely different academic programs.



For example:



```text

Environmental Economics

```



should not automatically become:



```text

Economics

```



Likewise:



```text

Computer Science and Engineering

```



should not automatically become:



```text

Computer Science

```



and:



```text

Consumer Science

```



should not automatically become:



```text

Family and Consumer Sciences

```



For this reason, broad fuzzy matching is disabled for program names.



Program standardization uses:



1. Whitespace normalization.

2. Documented deterministic corrections.

3. Exact case-insensitive canonical matching.

4. Preservation of the original value when no safe match exists.



This prioritizes semantic accuracy over maximizing the number of standardized values.



---



# 12. Conservative University Standardization



University names are more suitable for controlled fuzzy matching because many differences are caused by spelling, punctuation, capitalization, or formatting.



The workflow therefore allows university fuzzy matching only at a high confidence threshold.



Examples of appropriate standardization observed during validation include:



```text

university of british columbia

-> University of British Columbia

```



```text

Kings College London

-> King's College London

```



```text

University of Maryland Baltimore

-> University of Maryland, Baltimore

```



```text

San Jose State University

-> San Jose State University

```



These transformations standardize presentation while preserving the institution represented by the source value.



---



# 13. Standardization Validation



The final standardization run produced:



```text

Records standardized: 14,805

Missing program names: 4

Missing universities: 0

Program values changed: 489

University values changed: 141

Suspicious program reductions: 0

```



The `Suspicious program reductions: 0` check is particularly important because it provides a validation control against collapsing detailed program names into unrelated or overly broad canonical categories.



A sample from the final run includes:



```text

Environmental Economics

-> Environmental Economics



Global Health

-> Global Health



Public Policy

-> Public Policy



Engineering Science

-> Engineering Science



Mechanical Engineering

-> Mechanical Engineering



Computer Science

-> Computer Science



Computer Science and Engineering

-> Computer Science and Engineering



Neuroscience

-> Neuroscience



Consumer Science

-> Consumer Science



Economics

-> Economics

```



---



# 14. Output Fields



The standardized output retains the repaired source fields and adds standardized representations.



Important fields include:



```text

program_name

university

comments

date_added

entry_url

applicant_status

acceptance_date

rejection_date

start_term

student_type

gre_score

gre_v_score

degree

gpa

gre_aw

raw_listing

source_page

standardized_program_name

standardized_university

```



Keeping both the original repaired values and standardized values improves traceability.



For example:



```text

program_name

standardized_program_name

```



can be compared directly to determine whether standardization changed a value.



---



# 15. Reproducing the Processing Workflow



The already collected source dataset is included so the repair and cleaning workflow can be reproduced even when live GradCafe access is temporarily restricted.



Run the repair stage:



```powershell

python repair_applicant_data.py

```



Expected output includes approximately:



```text

Repaired applicant records: 14,805

Duplicate entry URLs: 0

Suspicious program names containing decision text: 0

```



Then run the standardization stage:



```powershell

python clean.py

```



Expected output includes:



```text

Records standardized: 14,805

Missing universities: 0

Suspicious program reductions: 0

```



The resulting standardized dataset is:



```text

llm_extend_applicant_data.json

```



---



# 16. Live Scraper Execution



The scraper can be run using:



```powershell

python scrape.py

```



When normal GradCafe result content is available, the scraper attempts to collect and validate applicant records.



If Cloudflare or another anti-bot challenge is returned, the scraper terminates safely and preserves the existing dataset.



This means that live website availability is not required to reproduce the repair and standardization stages from the existing source data.



---



# 17. Data Quality Principles



Several safeguards are used throughout the revised workflow.



### Preserve source data



The original collected dataset is retained instead of being overwritten during repair.



### Separate repair from standardization



Structural reconstruction and naming standardization are performed by different scripts.



### Preserve semantic meaning



Similar academic programs are not automatically treated as equivalent.



### Make transformations inspectable



Canonical lists and deterministic fixes are stored explicitly rather than hidden inside the workflow.



### Validate output



The scripts report missing fields, duplicate URLs, changed values, and suspicious transformations.



### Fail safely



A blocked or malformed live webpage cannot overwrite the existing applicant dataset.



---



# 18. Known Limitations



The dataset originates from user-submitted GradCafe information. Consequently, individual entries may contain missing, inconsistent, or self-reported values.



Not every applicant provides GPA, GRE, student type, or other optional information.



A small number of repaired records still have missing fields:



```text

Missing program names: 4

Missing degrees: 17

Missing start term: 1

```



These values are retained as missing rather than guessed.



The live GradCafe website may also use anti-bot protection. The project deliberately does not attempt to bypass those controls.



---



# 19. Final Result



The revised Module 2 workflow provides a traceable pipeline:



```text

Original Collected Data

&#x20;       |

&#x20;       v

Structural Validation

&#x20;       |

&#x20;       v

Applicant Record Repair

&#x20;       |

&#x20;       v

applicant_data_repaired.json

&#x20;       |

&#x20;       v

Conservative Standardization

&#x20;       |

&#x20;       v

Canonical / Deterministic Validation

&#x20;       |

&#x20;       v

llm_extend_applicant_data.json

```



The final dataset contains **14,805 reconstructed and standardized applicant records**.



Most importantly, the revised implementation addresses the original data-quality problem by ensuring that applicant detail fragments are associated with the correct primary listing and by preventing aggressive standardization from changing the meaning of legitimate program names.



---



## Author



Amr Mansour



Johns Hopkins University  

EN.605.256.81.SU26 - Modern Software Concepts in Python






