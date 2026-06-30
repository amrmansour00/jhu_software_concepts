# GradCafe Analytics – Module 6

## Project Overview

This project extends the GradCafe Analytics application into a containerized microservices architecture using Docker Compose, PostgreSQL, RabbitMQ, and Flask.

The system separates the web application from the background worker using asynchronous messaging. User requests are queued through RabbitMQ and processed independently by the worker service before updating the PostgreSQL database.

---

## Architecture

The application consists of four services:

- Web Service (Flask)
- Worker Service
- PostgreSQL Database
- RabbitMQ Message Broker

Workflow:

1. User clicks **Pull Data**
2. Flask publishes a message to RabbitMQ
3. Worker consumes the message
4. Worker processes applicant data
5. PostgreSQL is updated
6. User clicks **Update Analysis**
7. SQL analytics are refreshed

---

## Project Structure

```
Module_6/
│
├── src/
│   ├── web/
│   ├── worker/
│   ├── db/
│   └── data/
│
├── tests/
├── docs/
├── docker-compose.yml
├── requirements.txt
├── setup.py
├── README.md
```

---

## Installation

Clone the repository:

```bash
git clone <repository-url>
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Docker Deployment

Build containers:

```bash
docker compose build
```

Start all services:

```bash
docker compose up -d
```

Verify:

```bash
docker compose ps
```

---

## Running the Application

Open:

```
http://localhost:8080
```

or in GitHub Codespaces:

```
https://<codespace>-8080.app.github.dev
```

---

## Running Tests

```
pytest
```

---

## Code Quality

```
PYTHONPATH=src:src/web pylint src --fail-under=10
```

Current score:

```
10.00/10
```

---

## Documentation

Read the Docs:

https://jhu-software-concepts-amr.readthedocs.io/en/latest/

---

## Deliverables

Included:

- Docker Compose configuration
- Flask web service
- RabbitMQ worker
- PostgreSQL integration
- Pytest test suite
- Sphinx documentation
- GitHub repository
- Docker screenshots
- RabbitMQ screenshots
- Worker execution logs

---

## Evidence

Included in this submission:

- website_running.png
- docker_running.png
- rabbitmq_running.png
- worker_processed_tasks.png
- coverage_summary.txt
- pylint_score.txt
- docker_compose_status.txt
- worker_logs.txt

---

## License

Educational project submitted for the Johns Hopkins University Modern Software Concepts course.