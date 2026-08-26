# GradCafe Analytics - Module 7



## Project Overview



Module 7 extends the GradCafe Analytics project into a cloud deployment workflow using Amazon Web Services (AWS).



The project demonstrates how application data can be stored in Amazon S3, retrieved programmatically with Python and Boto3, and used alongside an EC2-hosted containerized GradCafe application.



The deployment builds on the microservices architecture developed in Module 6, including Flask, PostgreSQL, RabbitMQ, and a background worker.



\---



## Architecture



The Module 7 solution combines AWS cloud services with the existing GradCafe application architecture.



### AWS Components



\- Amazon S3 for dataset storage

\- Amazon EC2 for application hosting

\- AWS IAM and MFA for secure access

\- Boto3 for programmatic S3 access



### Application Components



\- Flask web service

\- RabbitMQ message broker

\- Background worker

\- PostgreSQL database

\- Docker Compose orchestration



### Data Flow



1. Applicant data is stored in Amazon S3.

2. `s3_fetch.py` connects to S3 using Boto3.

3. The dataset is downloaded to the configured application data location.

4. The containerized GradCafe environment runs on EC2.

5. Flask provides the web interface.

6. RabbitMQ handles asynchronous tasks.

7. The worker processes queued tasks.

8. PostgreSQL stores and supports analysis of applicant data.



\---



## Project Structure



```text

module_7/

|

|-- src/

|   `-- s3_fetch.py

|

|-- tests/

|   `-- test_s3_fetch.py

|

|-- ec2/

|   |-- docker-compose.ec2.yml

|   |-- EC2_DEPLOYMENT.md

|   `-- src/

|       |-- data/

|       |-- db/

|       |-- web/

|       `-- worker/

|

|-- applicant_data.json

|-- grad-cafe-pipeline.ipynb

|-- requirements.txt

|-- pytest.ini

|-- README.md

|

|-- daily_work.png

|-- ec2-compose-ps.png

|-- ec2_instance.png

|-- grad_cafe_bucket.png

|-- liveNotebook.png

|-- mfa.png

`-- web_8080.png


