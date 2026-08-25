# Module 6 - Containerized Microservices with Docker and RabbitMQ

## Overview

This project extends the GradCafe Analytics application into a containerized microservices architecture using Flask, PostgreSQL, RabbitMQ, Docker, and Docker Compose.

The application separates the web interface from background data processing through asynchronous messaging. The Flask web service publishes tasks to RabbitMQ, while an independent worker consumes and processes those tasks before updating PostgreSQL.

This architecture demonstrates service separation, asynchronous processing, container orchestration, automated testing, and software quality practices.

## Architecture

The application consists of four primary services:

- **Web Service** - Flask application providing the user interface and analytics actions.
- **Worker Service** - Background service that consumes RabbitMQ messages and processes data tasks.
- **PostgreSQL** - Persistent database used for applicant data and SQL analytics.
- **RabbitMQ** - Message broker used for asynchronous communication between the web service and worker.

### Processing Workflow

1. The user selects **Pull Data** in the Flask application.
2. The web service publishes a task to RabbitMQ.
3. RabbitMQ queues the task.
4. The worker consumes the task from the queue.
5. The worker processes the applicant data.
6. PostgreSQL is updated.
7. The user selects **Update Analysis**.
8. The application queries PostgreSQL and displays the refreshed analytics.

This design allows data processing to operate independently from the web request lifecycle.

## Project Structure

```text
module_6/
|
|-- src/
|   |-- db/
|   |   |-- __init__.py
|   |   `-- load_data.py
|   |
|   |-- web/
|   |   |-- publisher.py
|   |   |-- query_data.py
|   |   `-- run.py
|   |
|   |-- worker/
|   |   `-- consumer.py
|   |
|   `-- data/
|
|-- tests/
|   |-- conftest.py
|   |-- test_db_load_data.py
|   |-- test_publisher.py
|   `-- test_web.py
|
|-- docs/
|-- docker-compose.yml
|-- requirements.txt
|-- setup.py
|-- pytest.ini
`-- README.md
```

## Installation

Install the project dependencies with:

```bash
pip install -r requirements.txt
```

Important runtime dependencies include:

- Flask
- psycopg
- python-dotenv
- pika

Testing, documentation, and code-quality dependencies are also included in `requirements.txt`.

## Docker Deployment

Build the containers:

```bash
docker compose build
```

Start the services:

```bash
docker compose up -d
```

Verify that the containers are running:

```bash
docker compose ps
```

The Docker Compose environment coordinates the Flask web application, RabbitMQ message broker, worker service, and PostgreSQL database.

## Running the Application

After the containers are running, open:

```text
http://localhost:8080
```

When using GitHub Codespaces, use the forwarded port URL associated with port `8080`.

## RabbitMQ Processing

The web service uses `pika` to communicate with RabbitMQ.

When a data-processing request is initiated, the publisher sends a task to the message queue. The worker consumes the message and performs the background processing independently of the Flask request.

This provides asynchronous communication between the application components and reduces coupling between the web and processing services.

## Testing

Run the complete automated test suite with:

```bash
pytest -v
```

Run the tests with source coverage:

```bash
pytest --cov=src --cov-report=term-missing -v
```

Final validated test result:

```text
30 tests passed
97% overall source coverage
```

Coverage by source component:

| Component | Coverage |
| --- | ---: |
| `src/db/__init__.py` | 100% |
| `src/db/load_data.py` | 100% |
| `src/web/publisher.py` | 100% |
| `src/web/query_data.py` | 85% |
| `src/web/run.py` | 94% |
| `src/worker/consumer.py` | 97% |
| **Overall** | **97%** |

The tests cover database loading, RabbitMQ publishing and worker behavior, Flask web functionality, and supporting application logic.

## Code Quality

Pylint is used for static code-quality analysis.

Run:

```bash
pylint src --fail-under=10
```

Final validated result:

```text
10.00/10
```

## Documentation

Sphinx is used to generate project documentation.

Build the documentation with:

```bash
docs/make.bat clean
docs/make.bat html
```

The final Sphinx build completes successfully with no warnings.

The documentation includes:

- Setup instructions
- Architecture
- API reference
- Testing
- Operational notes

## Configuration and Security

Environment-specific configuration should not be committed to source control.

The project `.gitignore` excludes:

```text
.env
__pycache__/
*.pyc
.pytest_cache/
docs/build/
```

Credentials and database configuration should therefore be provided through environment variables or a local `.env` file rather than embedded in the source code.

## Evidence

The Module 6 submission includes supporting evidence such as:

- `website_running.png` - running Flask application
- `docker_running.png` - Docker services
- `rabbitmq_running.png` - RabbitMQ service
- `worker_processed_tasks.png` - worker task processing
- `coverage_summary.txt` - automated test and coverage results
- `pylint_score.txt` - Pylint quality score
- `docker_compose_status.txt` - Docker Compose service status
- `worker_logs.txt` - worker execution evidence

## Technologies

The project uses:

- Python
- Flask
- PostgreSQL
- psycopg
- RabbitMQ
- pika
- Docker
- Docker Compose
- Pytest
- pytest-cov
- Pylint
- Sphinx

## Learning Outcomes

Module 6 demonstrates how a Python application can evolve from a single application into a containerized, service-oriented architecture.

The implementation demonstrates:

- Separation of application responsibilities
- Asynchronous messaging with RabbitMQ
- Background worker processing
- PostgreSQL persistence
- Docker-based service isolation
- Multi-container orchestration with Docker Compose
- Automated testing and coverage analysis
- Static code-quality validation
- Generated technical documentation

## Course

Johns Hopkins University  
Modern Software Concepts  
Module 6