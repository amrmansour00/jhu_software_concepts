"""Database configuration and connection helpers."""

import os
from dataclasses import dataclass

import psycopg
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class DatabaseConfig:
    """Database configuration loaded from environment variables."""

    host: str
    port: int
    name: str
    user: str
    password: str
    sslmode: str = "require"

    @classmethod
    def from_environment(cls):
        """Build database configuration from environment variables."""
        required_values = {
            "DB_HOST": os.getenv("DB_HOST"),
            "DB_NAME": os.getenv("DB_NAME"),
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        }

        missing = [
            key for key, value in required_values.items()
            if not value
        ]

        if missing:
            raise ValueError(
                "Missing database environment variables: "
                + ", ".join(missing)
            )

        return cls(
            host=required_values["DB_HOST"],
            port=int(os.getenv("DB_PORT", "5432")),
            name=required_values["DB_NAME"],
            user=required_values["DB_USER"],
            password=required_values["DB_PASSWORD"],
            sslmode=os.getenv("DB_SSLMODE", "require"),
        )

    def as_dict(self):
        """Return connection parameters for psycopg."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.name,
            "user": self.user,
            "password": self.password,
            "sslmode": self.sslmode,
        }


def get_connection(config=None):
    """Create a PostgreSQL connection."""
    database_config = config or DatabaseConfig.from_environment()
    return psycopg.connect(**database_config.as_dict())
