# Test execution report

Execution date: 2026-09-28 (Asia/Kolkata). Executor: Codex assistant; these are not claims of manual execution by the learner.

## Environment
- macOS, Apple Silicon, Python 3.14.
- FastAPI 0.141.1, Starlette 1.7.0, Pytest 9.1.1, pytest-playwright 0.9.0, Playwright 1.63.0.
- Chromium / Chrome for Testing 153.0.8010.12 (Playwright build 1243), headless.
- Full installed dependency versions: `requirements-lock.txt`.
- Temporary SQLite databases; manual practice database not used by automation.

## Results
| Suite | Command / method | Actual result | Evidence |
|---|---|---|---|
| Application smoke | FastAPI TestClient: home, login, save, amount, history | Passed | Development terminal observation; no screenshot captured |
| API | `python -m pytest tests/api -q` | **44 passed, 1 warning in 13.00s** | `api-test-output.txt` |
| Browser, initial | `python -m pytest tests/browser -q` | **1 passed, 2 failed in 71.03s** | `browser-test-initial-output.txt` |
| Browser, after label correction | Same command | **3 passed in 3.85s** | `browser-test-output.txt` |
| Manual cases | TC01–TC25 | **NOT RUN: 0/25 executed** | Actual Result and Evidence remain empty |
| Postman execution | Collection supplied for learner | **NOT RUN** | No execution claimed |
| SQL query execution | Queries supplied for learner | **NOT RUN** | API tests independently query database counts |

The API suite ran on the application committed as `ef5c356`, with the tests saved in `da9f310`. The first browser run used application `ef5c356` and tests from `da9f310`. The successful rerun used those same tests plus the project-label HTML correction committed with this report. The backend did not change between these runs. Parametrized input combinations account for the 44 API executions.

## Observed browser failure and correction
The two timesheet browser tests timed out locating `get_by_label("Project", exact=True)`. The HTML wrapped the select and its option text inside the label, so the exact label lookup did not match. The fix separates the label from the select and explicitly associates it with `for="project"`. Both affected flows and login/logout passed on rerun. This was an observed UI-label/test-interaction issue, not evidence of failed billing or database integrity. Initial output is retained rather than overwritten.

## Warning
Starlette emitted a deprecation warning about TestClient's httpx integration and recommends httpx2. The installed combination executed all 44 tests successfully. A future dependency refresh should review this warning and rerun the suite. The exact working environment is recorded in the lock file.

## Coverage and remaining risks
API checks include login/registration validation, password hashing, expired/revoked sessions, assigned projects, integer boundaries, missing/invalid fields, zero inserts on rejection, billing, repeated/concurrent same-ID requests, independent intentional entries, employee isolation and restart persistence. Browser checks cover login/logout, billing with page refresh, and rapid double-clicking.

No manual PASS statuses, screenshots, Postman results or SQL execution results are fabricated. No load, full accessibility, cross-browser, production-security or organization-tenant testing was performed. Manual execution and release sign-off remain pending; this is a runnable learning deliverable, not a production QA approval.
