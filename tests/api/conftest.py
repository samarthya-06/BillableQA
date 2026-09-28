import sqlite3
import pytest
from fastapi.testclient import TestClient
from app.main import create_app


@pytest.fixture
def database(tmp_path):
    # Every test gets its own database; demo/manual records are never touched.
    return tmp_path / "test.db"


@pytest.fixture
def client(database):
    with TestClient(create_app(database)) as client:
        yield client


@pytest.fixture
def alice(client):
    response = client.post("/api/login", json={"email": "alice@example.com", "password": "DemoPass123!"})
    assert response.status_code == 200
    return client


@pytest.fixture
def row_count(database):
    def count(table="timesheets"):
        assert table in {"timesheets", "users"}
        with sqlite3.connect(database) as connection:
            return connection.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
    return count
