# Personally execute your first five manual cases

## Prepare once
1. Follow the README installation instructions, start the server and open http://127.0.0.1:8000.
2. Open `qa/MANUAL_TEST_CASES.csv`. Keep Actual Result and Evidence empty until you observe something.
3. Record your date, browser/OS and current commit (`git rev-parse --short HEAD`) in a copy of the execution report. These are your results, separate from the saved automation run.

## TC01 — valid login
1. In the **Welcome back** form, type `alice@example.com` and `DemoPass123!`.
2. Click **Log in**.
3. Expect the workspace and Alice's email. Check the project choices include Customer Portal and Billing API.
4. Write what you actually see in TC01's Actual Result. Mark PASS only if it matches. Click **Log out** for the next case.

## TC02 — missing email
1. Leave login email empty; type `DemoPass123!` in the password field.
2. Click **Log in**.
3. Expect browser validation on the empty email and no workspace. Wording varies by browser; the requirement is to prevent login.
4. Record the real outcome in TC02 and set its status.

## TC03 — missing password
1. Type `alice@example.com` as login email and clear the password completely.
2. Click **Log in**.
3. Expect password-field validation and no workspace.
4. Record the real outcome in TC03 and set its status.

## TC04 — incorrect password
1. Use `alice@example.com` and `WrongPass123!`.
2. Click **Log in**.
3. Expect “Invalid email or password.” and no authenticated workspace.
4. Record TC04's actual result and status.

## TC05 — successful registration at the password boundary
1. In **Create an account**, use `learner01@example.com` and `Learn123` (exactly 8 characters). If that email already exists, choose a fresh one and record it in Test Data.
2. Click **Register**. Expect “Account created. You can now log in.”
3. In the login form, enter that same email/password and click **Log in**.
4. Expect your new email and Customer Portal as the assigned project.
5. Record TC05's actual result and status. Log out when finished.

If actual differs from expected, mark FAIL, capture real evidence if helpful and copy the defect template. If you cannot execute because setup is broken, mark BLOCKED and state why. Do not copy expected text into actual without checking it. After these five attempts, update your manual execution count; do not mark the other 20 cases passed.
