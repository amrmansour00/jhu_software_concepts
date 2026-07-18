\# Module 10: Graduate Admissions Dashboard



\## Research Question



What factors appear to influence graduate admissions outcomes?



\## Dataset



This project uses the cleaned Grad Cafe graduate admissions dataset generated in previous modules. The dataset contains applicant information including degree type, admission outcome, GPA, start term, and applicant classification.



\## Project Files



\- `visualization.py` – Generates all required visualizations

\- `dashboard.py` – Creates and runs the interactive Dash dashboard

\- `acceptance\_by\_degree.png` – Seaborn visualization

\- `gpa\_by\_outcome.png` – Matplotlib visualization

\- `admissions\_by\_term.html` – Interactive Plotly visualization

\- `dashboard.png` – Dashboard screenshot

\- `requirements.txt` – Project dependencies

\- `final\_clustered\_data.csv` – Input dataset



\## Installation



Install the required dependencies:



```bash

pip install -r requirements.txt

```



\## Run Visualizations



Generate all required visualizations:



```bash

python visualization.py

```



\## Run Dashboard



Launch the interactive dashboard:



```bash

python dashboard.py

```



Open the dashboard in your browser:



```text

http://127.0.0.1:8050

```



\## Visualization 1: Graduate Admission Outcomes by Degree Type



!\[Acceptance by Degree](acceptance\_by\_degree.png)



This visualization compares admission outcomes across Master's and PhD applications. Master's applications show a substantially higher acceptance rate, while PhD applications experience a higher rejection rate.



\## Visualization 2: Applicant GPA Distribution by Admission Outcome



!\[GPA by Outcome](gpa\_by\_outcome.png)



This boxplot compares GPA distributions across accepted, rejected, and waitlisted applicants. The GPA distributions overlap considerably, suggesting GPA alone does not clearly separate admissions outcomes.



\## Visualization 3: Admission Outcomes by Start Term and Student Type



The interactive Plotly visualization is saved as:



`admissions\_by\_term.html`



This visualization explores how admission outcomes vary across start terms and applicant types (Domestic, International, and Other).



\## Dashboard



!\[Dashboard](dashboard.png)



The dashboard combines all analyses into a single interactive view and provides a concise summary of the findings.



\## Key Findings



1\. Master's applications have a substantially higher acceptance rate than PhD applications.

2\. GPA distributions overlap considerably across accepted, rejected, and waitlisted applicants.

3\. Application volume and outcome mix vary across start terms and student types.



\## Conclusion



Degree type appears to be more strongly associated with admissions outcomes than GPA alone. GPA distributions are very similar across admission outcomes, suggesting that additional applicant characteristics would be required to build a more predictive admissions model.



