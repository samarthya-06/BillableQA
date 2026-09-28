# Test plan

## Objective and scope
Check R01–R12 for a local employee timesheet SaaS example. Prioritize wrong billing, unauthorized access and duplicate records. Cover registration, sessions, assignments, validation, calculation, history and persistence at UI, API and database levels.

## Approach
1. Read requirements and implementation decisions before executing cases.
2. Run 25 manual cases; record only observed results. Use equivalence partitions for valid/invalid inputs and boundary values 0, 1, 12, 13 for hours and 7, 8, 9 for password length.
3. Use API tests to bypass browser restrictions and verify server enforcement plus database counts.
4. Use three browser checks for login, save/refresh and double-click behavior.
5. Compare UI/API values with the two SQL queries. Re-test fixes, then regress login, authorization, valid/invalid submissions, billing and persistence.

## Environment and data
Local Python 3.11+; SQLite; desktop Chromium. Install from README. Demo accounts have different assignments. Manual data persists in billableqa.db. Automated tests use temporary databases; never point automation at your manual database. Use fresh registration emails on repeat runs. No real employee/customer data.

## Entry and exit criteria
Entry: app starts, demo users exist, requirements and test data are available.
Exit for a learning release: API suite passes, browser execution is recorded honestly, all P1 manual cases are executed with no unresolved critical/high defects, and remaining risks are documented. Until manual execution happens this is a runnable study, not a QA-approved release.

## Defect handling
Record reproducible expected/actual behavior with environment, evidence and severity. Severity describes impact; priority describes urgency. Re-test the same failure after a fix. Do not invent defects just to fill a report.

## Exclusions and risks
No load, penetration, full accessibility, cross-browser certification, production hosting, password recovery, email verification or organizational tenant model. Browser validation differs by browser. Three browser tests provide a small smoke suite, not complete coverage. Request-ID deduplication protects retries of one action, not distinct requests using distinct IDs.
