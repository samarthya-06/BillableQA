# Explaining BillableQA in a campus interview

## A short introduction you can adapt after practicing

“BillableQA is a small timesheet application I used to learn software testing. An employee logs in, chooses an assigned project, enters a date and whole working hours, and sees the billable amount. I used AI assistance to build this learning project. My focus is understanding requirements, designing tests, executing them honestly and checking results at the UI, API and database levels. I am still learning to write the code independently.”

Only add claims about tests you have personally executed. The included run report distinguishes assistant-executed automation from your pending manual work.

## What makes this a QA case study?

The product is deliberately small so the testing is visible. A correct-looking page is not enough: an invalid request must not insert a hidden database row, and Bob must not see Alice's records. The highest-impact risks are incorrect billing, unauthorized access and duplicate entries.

Start with R07: hours must be an integer from 1 through 12. Valid inputs form one equivalence partition; zero/negative numbers, values above 12 and fractions are invalid partitions. Boundary value analysis selects 0, 1, 12 and 13 because mistakes often occur at the limits. A 1.5-hour request checks the separate whole-number rule.

For R10, use an independent expected value: 3 × $75 = $225. Check the UI and API, then the stored cents value (22500). Do not merely copy the application's answer into Expected Result.

## How to explain the test layers

- Manual UI test: use the form as an employee and observe messages, project choices and saved history.
- API test: send a request directly, including values the browser blocks. This verifies the server enforces the rule.
- Database validation: compare row counts before/after a rejected action and inspect stored calculations.
- Browser automation: repeat a few important user journeys using Playwright. It is useful regression coverage but does not replace exploratory testing.

A requirement is the rule. A scenario is what to check. A test case supplies steps/data and an expected result. A defect report records a real mismatch. The traceability matrix shows which cases cover each rule; coverage does not mean execution or success.

## Read one small test without memorizing everything

Open `tests/api/test_api.py` and find `test_invalid_hours`. The fixture logs Alice in against a temporary database. The test sends hours such as 0 or 13. `assert response.status_code == 422` checks rejection; `assert row_count() == 0` checks there was no hidden write. Parametrization repeats this logic for multiple invalid values.

A fixture is reusable preparation and cleanup. An assertion asks “does actual equal expected?” You do not need to claim you can write the entire fixture independently to explain its purpose.

## Questions you may be asked

**Why validate both in the browser and server?** Browser checks help the user fix mistakes quickly. A client can bypass them, so the server must independently protect data.

**Authentication versus authorization?** Authentication establishes who is logged in. Authorization decides which projects and records that employee may access.

**How are duplicate submissions prevented?** The button is disabled during saving. The request also includes an action ID; repeating the same ID returns the existing record. A transaction and unique database constraint protect concurrent requests. Identical content with a new action ID is intentionally a different entry because the requirements do not prohibit multiple entries per day.

**How do you check persistence?** Save a row, record its ID and amount, refresh, and verify the same row remains. The API suite additionally checks reopening the app against the same database.

**What is regression testing?** After a change, check existing important behavior still works. Re-testing repeats the specific failed case after its fix; regression looks for side effects elsewhere.

**Severity versus priority?** Severity measures impact, while priority schedules urgency. A hypothetical wrong billing calculation has high impact; it is not an observed defect in this project unless reproduced.

**Why SQLite and integer cents?** SQLite keeps setup local and simple. Integer cents avoid floating-point rounding surprises for whole hours and fixed cent-denominated rates.

**What are the limitations?** This has only two demo employee roles with assignments, no organization tenant model, three browser tests, and no load/security certification. Manual cases are initially NOT RUN. More tests and production hardening would be needed for a real B2B SaaS release.

## A practical study order tonight

1. Launch the app and personally execute TC01–TC05.
2. Try hour boundaries 0, 1, 12, 13; calculate an expected bill yourself.
3. Log in as Bob to understand record ownership.
4. Run the API suite and read one parametrized test.
5. Watch the three browser tests in headed mode.
6. Explain the two SQL queries and one potential defect report without claiming a defect exists.

If you cannot explain a line yet, say “I used assistance for that part; I understand its purpose and am learning the implementation.” That is more useful than memorizing an inflated experience claim.
