# BillableQA requirements

- R01: Email and password are mandatory for login.
- R02: Registration requires a valid and unique email.
- R03: Password must contain at least 8 characters.
- R04: Only authenticated employees can access their timesheets.
- R05: Employees can select only projects assigned to them.
- R06: Project selection and working date are mandatory.
- R07: Working hours must be an integer between 1 and 12 inclusive.
- R08: Invalid timesheet submissions must not create database records.
- R09: One intentional submission must create exactly one record. Rapid double-clicking must not create unintended duplicates.
- R10: Billable amount = working hours × project hourly rate.
- R11: Employees must only view their own timesheet records.
- R12: Valid records must persist after a page refresh.

## Explicit implementation decisions
- Password minimum applies to registration; login checks existing credentials. Passwords are not trimmed.
- Email uniqueness is case-insensitive. The server validates email format.
- USD demo rates: Customer Portal $50/hour; Billing API $75/hour; Analytics Dashboard $60/hour.
- Alice is assigned projects 1 and 2; Bob is assigned project 3. New accounts are assigned project 1.
- Dates must be valid calendar dates; no past/future restriction was specified.
- Multiple intentional entries for the same project/date are allowed. An intentional submission has a UUID. Retrying that UUID returns the original row; different details with the same UUID return 409.
- Server checks all business rules even if browser validation is bypassed. A database unique constraint also protects against concurrent duplicate requests.
- Sessions last 8 hours. The local HTTP demo uses an HttpOnly, SameSite=Strict cookie; production hardening is outside this case study.
- Amount and rate are stored as integer cents. The rate is copied into each entry so history stays consistent.
