"""Small teaching app: routes, SQLite and sessions in one readable module."""
from contextlib import asynccontextmanager, contextmanager
from datetime import date
import hashlib
import hmac
import os
from pathlib import Path
import secrets
import sqlite3
import time
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, StrictInt

STATIC = Path(__file__).parent / "static"


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000)
    return salt + ":" + digest.hex()


def password_matches(password, stored):
    return hmac.compare_digest(hash_password(password, stored.split(":")[0]), stored)


class Registration(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Login(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1, max_length=128)


class Timesheet(BaseModel):
    project_id: StrictInt
    working_date: date
    hours: StrictInt = Field(ge=1, le=12)
    submission_id: UUID  # Reuse this ID when retrying the same intentional submission.


def create_app(db_path=None):
    database = str(db_path or os.environ.get("BILLABLEQA_DB", "billableqa.db"))

    @contextmanager
    def db():
        connection = sqlite3.connect(database, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @asynccontextmanager
    async def lifespan(app):
        with db() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL, rate_cents INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS assignments (
                    user_id INTEGER REFERENCES users(id), project_id INTEGER REFERENCES projects(id),
                    PRIMARY KEY (user_id, project_id));
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY, user_id INTEGER REFERENCES users(id), expires INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS timesheets (
                    id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
                    project_id INTEGER NOT NULL REFERENCES projects(id), working_date TEXT NOT NULL,
                    hours INTEGER NOT NULL CHECK (typeof(hours) = 'integer' AND hours BETWEEN 1 AND 12),
                    rate_cents INTEGER NOT NULL, amount_cents INTEGER NOT NULL,
                    submission_id TEXT NOT NULL, UNIQUE (user_id, submission_id));
            """)
            for email in ("alice@example.com", "bob@example.com"):
                if not conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone():
                    conn.execute("INSERT INTO users(email,password_hash) VALUES (?,?)", (email, hash_password("DemoPass123!")))
            conn.executemany("INSERT OR IGNORE INTO projects VALUES (?,?,?)", [(1,"Customer Portal",5000),(2,"Billing API",7500),(3,"Analytics Dashboard",6000)])
            for email, projects in [("alice@example.com",[1,2]),("bob@example.com",[3])]:
                uid = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()[0]
                conn.executemany("INSERT OR IGNORE INTO assignments VALUES (?,?)", [(uid,pid) for pid in projects])
        yield

    app = FastAPI(title="BillableQA", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=STATIC), name="static")

    def current_user(request: Request):
        token = request.cookies.get("session", "")
        with db() as conn:
            user = conn.execute("""SELECT users.id, users.email FROM sessions JOIN users ON users.id=sessions.user_id
                WHERE token_hash=? AND expires>?""", (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
        if not user:
            raise HTTPException(401, "Please log in.")
        return dict(user)

    @app.get("/")
    def home():
        return FileResponse(STATIC / "index.html")

    @app.post("/api/register", status_code=201)
    def register(data: Registration):
        try:
            with db() as conn:
                cursor = conn.execute("INSERT INTO users(email,password_hash) VALUES (?,?)", (str(data.email).lower(), hash_password(data.password)))
                conn.execute("INSERT INTO assignments VALUES (?,1)", (cursor.lastrowid,))
        except sqlite3.IntegrityError:
            raise HTTPException(409, "Email is already registered.")
        return {"message": "Account created. You can now log in."}

    @app.post("/api/login")
    def login(data: Login, response: Response, request: Request):
        with db() as conn:
            user = conn.execute("SELECT * FROM users WHERE email=?", (data.email.strip().lower(),)).fetchone()
            if not user or not password_matches(data.password, user["password_hash"]):
                raise HTTPException(401, "Invalid email or password.")
            old_token = request.cookies.get("session", "")
            conn.execute("DELETE FROM sessions WHERE token_hash=? OR expires<=?", (hashlib.sha256(old_token.encode()).hexdigest(), int(time.time())))
            token = secrets.token_urlsafe(32)
            conn.execute("INSERT INTO sessions VALUES (?,?,?)", (hashlib.sha256(token.encode()).hexdigest(), user["id"], int(time.time())+28800))
        response.set_cookie("session", token, httponly=True, samesite="strict", max_age=28800)
        return {"email": user["email"]}

    @app.post("/api/logout")
    def logout(request: Request, response: Response):
        token = request.cookies.get("session", "")
        with db() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash=?", (hashlib.sha256(token.encode()).hexdigest(),))
        response.delete_cookie("session")
        return {"message": "Logged out."}

    @app.get("/api/me")
    def me(user=Depends(current_user)):
        return user

    @app.get("/api/projects")
    def projects(user=Depends(current_user)):
        with db() as conn:
            rows = conn.execute("""SELECT projects.* FROM projects JOIN assignments ON projects.id=assignments.project_id
                WHERE user_id=? ORDER BY projects.id""", (user["id"],)).fetchall()
        return [dict(row) for row in rows]

    @app.get("/api/timesheets")
    def history(user=Depends(current_user)):
        with db() as conn:
            rows = conn.execute("""SELECT t.*, p.name AS project_name FROM timesheets t JOIN projects p ON p.id=t.project_id
                WHERE t.user_id=? ORDER BY t.id DESC""", (user["id"],)).fetchall()
        return [dict(row) for row in rows]

    @app.post("/api/timesheets", status_code=201)
    def submit(data: Timesheet, response: Response, user=Depends(current_user)):
        with db() as conn:
            # Serialize the check + insert; the UNIQUE constraint is a second safety net.
            conn.execute("BEGIN IMMEDIATE")
            project = conn.execute("""SELECT p.* FROM projects p JOIN assignments a ON a.project_id=p.id
                WHERE a.user_id=? AND p.id=?""", (user["id"], data.project_id)).fetchone()
            if not project:
                raise HTTPException(403, "This project is not assigned to you.")
            existing = conn.execute("SELECT * FROM timesheets WHERE user_id=? AND submission_id=?", (user["id"], str(data.submission_id))).fetchone()
            if existing:
                if (existing["project_id"], existing["working_date"], existing["hours"]) != (data.project_id, data.working_date.isoformat(), data.hours):
                    raise HTTPException(409, "Submission ID already used with different details.")
                response.status_code = 200
                return dict(existing)
            cursor = conn.execute("""INSERT INTO timesheets(user_id,project_id,working_date,hours,rate_cents,amount_cents,submission_id)
                VALUES (?,?,?,?,?,?,?)""", (user["id"],data.project_id,data.working_date.isoformat(),data.hours,project["rate_cents"],data.hours*project["rate_cents"],str(data.submission_id)))
            return dict(conn.execute("SELECT * FROM timesheets WHERE id=?", (cursor.lastrowid,)).fetchone())

    return app


app = create_app()
