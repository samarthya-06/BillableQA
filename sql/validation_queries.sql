-- Run from the project folder: sqlite3 -header -column billableqa.db
-- Query 1: inspect saved rows, owner and stored billing calculation.
-- Every calculation_check should be OK. Rates/amounts are in cents.
SELECT t.id, u.email, p.name AS project, t.working_date, t.hours,
       t.rate_cents, t.amount_cents,
       CASE WHEN t.amount_cents = t.hours * t.rate_cents THEN 'OK' ELSE 'MISMATCH' END AS calculation_check
FROM timesheets t JOIN users u ON u.id = t.user_id
JOIN projects p ON p.id = t.project_id
ORDER BY t.id;

-- Query 2: count records for one employee before/after an action.
-- Invalid action: count unchanged; new valid action: +1; same-ID retry: unchanged.
-- Replace the email if checking Bob or a newly registered employee.
SELECT u.email, COUNT(t.id) AS record_count,
       COUNT(DISTINCT t.submission_id) AS distinct_submissions
FROM users u LEFT JOIN timesheets t ON t.user_id = u.id
WHERE u.email = 'alice@example.com'
GROUP BY u.id, u.email;
