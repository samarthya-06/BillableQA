"""API tests bypass HTML validation and check the server's business rules."""
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from app.main import create_app, password_matches


def entry(**changes):
    body = {"project_id": 1, "working_date": "2026-09-28", "hours": 2, "submission_id": str(uuid4())}
    body.update(changes)
    return body


@pytest.mark.parametrize("body", [{}, {"email":"alice@example.com"}, {"password":"DemoPass123!"}, {"email":"", "password":"DemoPass123!"}, {"email":"alice@example.com", "password":""}])
def test_login_required(client, body):
    assert client.post("/api/login", json=body).status_code == 422
    assert client.get("/api/me").status_code == 401  # Invalid input must not authenticate.


def test_wrong_password(client):
    assert client.post("/api/login", json={"email":"alice@example.com","password":"WrongPass123!"}).status_code == 401
    assert client.get("/api/me").status_code == 401


@pytest.mark.parametrize("password", ["Learn123", "Learn1234"])
def test_registration_valid(client, database, row_count, password):
    before = row_count("users")
    body = {"email":"learner@example.com", "password":password}
    assert client.post("/api/register", json=body).status_code == 201
    assert row_count("users") == before + 1
    with sqlite3.connect(database) as conn:
        stored = conn.execute("SELECT password_hash FROM users WHERE email=?", (body["email"],)).fetchone()[0]
    assert stored != password  # The database must never store the plain password.
    assert password_matches(password, stored)
    assert client.post("/api/login", json=body).status_code == 200
    assert [p["id"] for p in client.get("/api/projects").json()] == [1]


@pytest.mark.parametrize("body", [
    {"email":"invalid","password":"Learn123"},
    {"email":"learner@example.com","password":"Learn12"},
    {"email":"","password":"Learn123"},
    {"email":"learner@example.com","password":""},
    {"password":"Learn123"}, {"email":"learner@example.com"},
])
def test_registration_invalid(client, row_count, body):
    before = row_count("users")
    assert client.post("/api/register", json=body).status_code == 422
    assert row_count("users") == before


def test_registration_duplicate(client, row_count):
    before = row_count("users")
    assert client.post("/api/register", json={"email":"ALICE@example.com","password":"Learn123"}).status_code == 409
    assert row_count("users") == before


def test_authentication_required(client, row_count):
    for route in ("/api/timesheets", "/api/projects", "/api/me"):
        assert client.get(route).status_code == 401
    assert client.post("/api/timesheets", json=entry()).status_code == 401
    assert row_count() == 0


def test_logout_revokes_session(alice):
    token = alice.cookies.get("session")
    assert alice.post("/api/logout").status_code == 200
    alice.cookies.set("session", token)
    assert alice.get("/api/timesheets").status_code == 401  # Even replaying the old cookie fails.


def test_session_expiry(alice, database):
    with sqlite3.connect(database) as conn:
        conn.execute("UPDATE sessions SET expires=0")
    assert alice.get("/api/timesheets").status_code == 401


def test_project_authorization(alice, row_count):
    assert [p["id"] for p in alice.get("/api/projects").json()] == [1, 2]
    for project in (3, 999):
        assert alice.post("/api/timesheets", json=entry(project_id=project)).status_code == 403
    assert row_count() == 0


@pytest.mark.parametrize("hours", [0, 13, -1, 1.5, "2", True, None])
def test_invalid_hours(alice, row_count, hours):
    assert alice.post("/api/timesheets", json=entry(hours=hours)).status_code == 422
    assert row_count() == 0  # A rejected request must not leave a hidden row.


@pytest.mark.parametrize("missing", ["project_id", "working_date", "hours", "submission_id"])
def test_missing_fields(alice, row_count, missing):
    body = entry(); del body[missing]
    assert alice.post("/api/timesheets", json=body).status_code == 422
    assert row_count() == 0


@pytest.mark.parametrize("changes", [{"working_date":"2026-02-30"}, {"working_date":""}, {"project_id":""}, {"project_id":True}, {"submission_id":"not-a-uuid"}])
def test_invalid_fields(alice, row_count, changes):
    assert alice.post("/api/timesheets", json=entry(**changes)).status_code == 422
    assert row_count() == 0


@pytest.mark.parametrize("project,hours,expected", [(1,1,5000),(1,12,60000),(2,3,22500),(2,12,90000)])
def test_calculation_and_single_record(alice, row_count, project, hours, expected):
    response = alice.post("/api/timesheets", json=entry(project_id=project,hours=hours))
    assert response.status_code == 201
    assert response.json()["amount_cents"] == expected  # Cents, not floating-point dollars.
    assert row_count() == 1
    saved = alice.get("/api/timesheets").json()
    assert saved[0]["amount_cents"] == expected
    assert saved[0]["id"] == response.json()["id"]


def test_retry_is_idempotent(alice, row_count):
    body = entry()
    first = alice.post("/api/timesheets", json=body)
    retry = alice.post("/api/timesheets", json=body)
    assert first.status_code == 201
    assert retry.status_code == 200
    assert first.json()["id"] == retry.json()["id"]
    assert row_count() == 1
    body["hours"] = 3
    assert alice.post("/api/timesheets", json=body).status_code == 409
    assert row_count() == 1
    assert alice.get("/api/timesheets").json()[0]["hours"] == 2


def test_concurrent_retry(alice, row_count):
    body = entry()
    def submit(_):
        return alice.post("/api/timesheets", json=body)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(submit, range(2)))
    assert sorted(r.status_code for r in responses) == [200,201]
    assert len({r.json()["id"] for r in responses}) == 1
    assert row_count() == 1  # Simultaneous requests still create only one row.


def test_separate_intentions_allowed(alice, row_count):
    assert alice.post("/api/timesheets", json=entry()).status_code == 201
    assert alice.post("/api/timesheets", json=entry()).status_code == 201
    assert row_count() == 2  # Same date/project is allowed when the action IDs differ.


def test_history_isolation(alice):
    first = alice.post("/api/timesheets", json=entry()).json()
    alice.post("/api/logout")
    assert alice.post("/api/login", json={"email":"bob@example.com","password":"DemoPass123!"}).status_code == 200
    assert [p["id"] for p in alice.get("/api/projects").json()] == [3]
    assert alice.get("/api/timesheets?user_id=1").json() == []
    bob = alice.post("/api/timesheets", json=entry(project_id=3)).json()
    rows = alice.get("/api/timesheets").json()
    assert [r["id"] for r in rows] == [bob["id"]]
    assert first["id"] not in [r["id"] for r in rows]


def test_persistence_after_restart(alice, database):
    saved = alice.post("/api/timesheets", json=entry()).json()
    with TestClient(create_app(database)) as restarted:
        assert restarted.post("/api/login", json={"email":"alice@example.com","password":"DemoPass123!"}).status_code == 200
        rows = restarted.get("/api/timesheets").json()
        assert rows[0]["id"] == saved["id"]
        assert rows[0]["amount_cents"] == saved["amount_cents"]
