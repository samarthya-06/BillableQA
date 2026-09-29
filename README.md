# BillableQA — Mini SaaS Quality Engineering Case Study

A small, local employee timesheet app for learning software testing before a campus interview. It uses Python, FastAPI, SQLite, plain HTML/CSS/JavaScript, Pytest and Python Playwright. No cloud deployment is needed.

This is an AI-assisted learning project. Use it to practice executing tests, reading code and explaining observed behavior. Do not present generated code or unexecuted manual cases as independent professional experience.

<img width="1440" height="859" alt="image" src="https://github.com/user-attachments/assets/11a925c9-feaa-4b4d-99ac-2a2005c128db" />

<img width="1440" height="820" alt="image" src="https://github.com/user-attachments/assets/9db74c68-7aab-4735-962e-48ecfa43ddf4" />




## 1. Install and launch

Install Python 3.11 or newer. Open a terminal **inside the BillableQA folder** (the folder containing this README).

macOS / Linux:
```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m uvicorn app.main:app --reload
```

Windows PowerShell:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m uvicorn app.main:app --reload
```

If PowerShell blocks activation, invoke `.\.venv\Scripts\python.exe` in place of `python`; activation is optional. `requirements.txt` lists the direct dependencies; `requirements-lock.txt` records the exact versions used for the saved execution. The recorded environment is Python 3.14 on macOS; other Python/OS combinations are not certified by this run.

Open <http://127.0.0.1:8000>. API documentation is at <http://127.0.0.1:8000/docs>. Stop the server with Ctrl+C. The first launch creates `billableqa.db` in the current folder and seeds two users and three projects. Restarting preserves records. Do not delete your database unless you intentionally want to discard your local practice data.

If port 8000 is occupied, add `--port 8001` and use that port in the browser and Postman. If an import is missing, ensure commands use this project's virtual environment.

## 2. Demo accounts and rates

| Employee | Password | Assigned projects |
|---|---|---|
| alice@example.com | DemoPass123! | Customer Portal ($50/hour), Billing API ($75/hour) |
| bob@example.com | DemoPass123! | Analytics Dashboard ($60/hour) |

Newly registered users receive Customer Portal. These credentials are deliberately public demo data. All amounts are USD. For example, 3 hours × $75 = $225.

## 3. Understand the small app

- `app/main.py`: request validation, password hashing, session cookies, SQLite tables and API routes.
- `app/static/`: the page, its styling and the JavaScript that sends requests.
- `qa/`: requirements, plan, 25 manual cases, traceability, execution report and release checklist.
- `tests/api/`: direct HTTP tests; every test gets a new temporary SQLite database.
- `tests/browser/`: exactly three UI tests with a temporary server/database per test.
- `postman/`: importable requests; `sql/`: two validation queries.

The browser sends JSON → FastAPI checks the session and inputs → SQLite stores a row → the browser displays history. The server reads the user's ID from the session, never from a user-selected employee ID.

Passwords are salted PBKDF2-SHA256 hashes, not plain text. The browser receives a random HttpOnly session cookie; only its hash is stored in SQLite. Sessions expire after 8 hours and logout removes them. Money uses integer cents. Foreign keys, a transaction and a unique `(user_id, submission_id)` constraint support record integrity.

For a double-click, the browser disables Save while the request is pending. It also sends a UUID identifying the intentional action. The server returns the original row when the same ID is retried. A fresh intentional entry uses a new UUID, even if its date and hours are identical. On an uncertain network error, retry the unchanged form first. If you get a submission-ID conflict, refresh to inspect history before deciding whether a new entry is needed.

This is a local teaching app. It does not implement password recovery, email verification, rate limiting, a tenant/organization model, production HTTPS configuration or production security certification.

## 4. Execute manual tests

Read `qa/REQUIREMENTS.md`, then `qa/TEST_PLAN.md`. Open `qa/MANUAL_TEST_CASES.csv` in a spreadsheet or text editor. Start with [the first-five walkthrough](qa/FIRST_FIVE_MANUAL_TESTS.md).

For each case:
1. Establish its preconditions (especially which user is logged in).
2. Note the history row count before submissions.
3. Follow the steps with the supplied data.
4. Compare observed behavior with Expected Result.
5. Fill Actual Result with what happened; change Status to PASS, FAIL or BLOCKED only after attempting it. Keep Evidence blank unless you captured something real.

All 25 supplied rows initially have empty Actual Result/Evidence and Status `NOT RUN`. Automated results do not change these manual statuses. Use a new email when repeating registration cases.

## 5. Run the API tests

In another terminal in this folder, activate the environment, then:
```sh
python -m pytest tests/api -q
```

Or `python -m pytest` runs only the API suite by default. You do not need a running app for these tests. A fixture creates a temporary database and FastAPI TestClient. A test sends a request and uses `assert` to compare the actual response/database state with an expected value. Parametrization repeats the same test with different data; this is why the execution count is larger than the number of functions.

To study one example:
```sh
python -m pytest tests/api/test_api.py -k invalid_hours -v
```

See `qa/TEST_EXECUTION_REPORT.md` and the saved raw output for actual results. The installed Starlette version emits a deprecation warning about TestClient's httpx integration; it does not fail this recorded run.

## 6. Run the three browser tests

Install Chromium once, then run:
```sh
python -m playwright install chromium
python -m pytest tests/browser -q
```

Watch them run with:
```sh
python -m pytest tests/browser --headed --slowmo 300
```

The tests start their own server on a free local port; the manual app can remain open. They check login/logout, save/calculation/refresh, and rapid double-clicking. Each test has an isolated database. A failed run can capture real evidence with:
```sh
python -m pytest tests/browser --screenshot only-on-failure --tracing retain-on-failure
```

Artifacts go into the ignored `test-results/` directory. Browser installation needs internet access. Never mark browser tests passed just because the files exist.

## 7. Try Postman

Import `postman/BillableQA.postman_collection.json`. Start the manual app first. The collection's `base_url` defaults to `http://127.0.0.1:8000`. Run Log in as Alice; Postman's cookie jar keeps the session. Then request Assigned projects, Save timesheet and Timesheet history.

A fresh UUID produces 201 Created. Sending the identical body again returns 200 and the same row ID. The collection uses a fixed UUID deliberately so retries are easy to observe. Change its `submission_id` variable for a genuinely new action. Generate one with:
```sh
python -c "import uuid; print(uuid.uuid4())"
```

To check authorization, clear the cookie jar or log out. To check Bob, edit the login request's email. To check server validation, submit `hours: 13`, `hours: 1.5`, a missing field, or an unassigned project. Expect 422 for invalid data, 403 for an unassigned project, and no new database rows. Unknown/incorrect credentials return 401; duplicate registration returns 409. These requests have not been manually executed in Postman for you.

## 8. Inspect SQLite

The manual database is `billableqa.db`. With the SQLite command-line tool installed, run:
```sh
sqlite3 -header -column billableqa.db < sql/validation_queries.sql
```

Or open it interactively:
```sh
sqlite3 billableqa.db
.tables
.schema timesheets
.read sql/validation_queries.sql
.quit
```

If the SQLite command is unavailable, Python already includes SQLite:
```sh
python -c "import sqlite3; c=sqlite3.connect('billableqa.db'); print(c.execute('SELECT id, hours, amount_cents FROM timesheets').fetchall()); c.close()"
```

Query 1 checks each stored calculation and owner. Query 2 counts Alice's rows: note it before and after an invalid/valid/retried action. A duplicate check returning no discrepancy does not prove all possible duplicate scenarios; pair it with the action and row-count check. Do not share session tokens, password hashes or your practice database as evidence.

## 9. Document a real defect

Copy `qa/BUG_REPORT_TEMPLATE.md` into a new report only when you observe a discrepancy. Include reproducible steps, expected versus actual result, the relevant requirement, build/commit, environment and real evidence. Severity is the impact; priority is how urgently it should be fixed. An unexpected value is a candidate defect until you confirm the requirement and reproduce it.

After a fix, repeat the exact failed steps (re-test). Then test nearby behavior (regression): login; valid save; 0/1/12/13 hours; double-click; amount; refresh; Bob's isolation; logout. Re-run the API and browser suites. Record the new results rather than overwriting earlier evidence without context.

## 10. Interview preparation and honest scope

Read [INTERVIEW_EXPLANATION.md](INTERVIEW_EXPLANATION.md). Practice explaining one requirement, one boundary case, one API assertion and one SQL check. Personally execute cases before claiming you tested them. See the execution report for remaining coverage gaps. The Git history follows meaningful app, QA, automation and learning milestones; it is not a claim of long-term professional experience.

References used for the test setup: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/), [FastAPI lifespan testing](https://fastapi.tiangolo.com/advanced/testing-events/), and [Playwright's Python Pytest plugin](https://playwright.dev/python/docs/test-runners).
