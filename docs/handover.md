# Redgum Tutoring — Sprint Handover

## 1. What was delivered against scope

| Capability | Jira story | Notes |
|------------|-----------|-------|
| Login with administrator and tutor roles | RG-02 | Signed session cookie, bcrypt passwords |
| Administrator maintains students | RG-03 | Add, search, edit, deactivate; name, year level and family contact required |
| Administrator maintains tutors | RG-04 | Add, edit, deactivate; subjects recorded; deactivated tutors cannot be booked |
| Administrator maintains availability windows | RG-05 | Day, start and end per window; several windows per tutor |
| Booking a session with the availability rule | RG-06 | 60 or 90 minutes; must fit entirely inside one window for that day, with a clear refusal message |
| Moving, cancelling and marking sessions | RG-07 | Re-checks availability on move; cancelled sessions stay visible; attended and missed recorded |
| Day and week schedule, student history | RG-08 | Filter by tutor; a student's past and future sessions are listed |
| Tutor view of their own sessions | RG-09 | Only the signed-in tutor's upcoming sessions |
| Seed data, README, handover, backlog | RG-10 | Runs from a clean checkout with Python only |

All acceptance criteria are covered by automated tests (`pytest`); the availability rule has
its own unit test file (`tests/test_availability_rule.py`).

## 2. What was not delivered, and why

Everything below was asked for by Helen, Deb or Tomás, or appears in the paper documents, but
is out of scope for this sprint. All items sit in the product backlog (`docs/jira-import.csv`).

| Requested | Source | Why parked |
|-----------|--------|-----------|
| Room allocation and room clash detection | Deb, brief | Explicitly out of scope in the brief |
| Detecting overlapping or double bookings | Brief | Explicitly out of scope in the brief |
| Invoices, fees, prepaid packs and payments | Helen, Deb | Explicitly out of scope |
| Tutor timesheets and payroll | Helen, Tomás | Explicitly out of scope |
| SMS or email reminders | Helen | Explicitly out of scope |
| Parent portal and self-service booking | Helen | Explicitly out of scope |
| Video session links | Brief | Explicitly out of scope |
| Blue card expiry tracking | Helen | Explicitly out of scope |
| Accounting reports / Xero | Helen | Explicitly out of scope |
| January intensive, NAPLAN workshops, pizza night | Helen | Not part of the scheduling problem |
| Term unavailability (e.g. Tomás away week 8) | Availability card | Needs a date-specific absence model; next sprint |
| Tutor weekly session cap (8 sessions) | Availability card | A policy rule, not required by the sprint stories |
| "Students who have not booked in three weeks" report | Helen | Reporting is backlog |
| Printing the week per tutor | Deb | The schedule page can be printed from the browser; a dedicated print view is backlog |

## 3. Setup and run instructions from GitHub

See `README.md`. In short: install Python 3.10+, then

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://localhost:8000>. Tests: `pytest`. No database, Node or Docker install is needed.

## 4. Known issues and limitations

1. Sessions are checked against availability only; overlaps between sessions are not detected
   (deliberate — the brief excludes it). Two students can still be booked with one tutor at the
   same time.
2. Availability is stored per weekday and does not know about term dates or school holidays.
   A tutor who is away for one week cannot be marked away; their window would have to be edited.
3. Session states are final: a cancelled, attended or missed session cannot be moved or
   re-opened.
4. Only 60 and 90 minute sessions are accepted (the brief states these are the only lengths).
5. The sign-in form has no CSRF token (the session cookie is `SameSite=Lax`), no rate limiting
   and no password reset. Suitable for the centre's internal use and this course, not for the
   public internet as-is.
6. There is no audit log of who changed what.
7. SQLite suits the centre's scale and a course demonstration; a multi-user deployment would
   want a server database and concurrent-write handling.
8. Lists are filtered by search and date rather than paginated; fine at 140 students and 11
   tutors.
9. The frontend has no automated tests; behaviour is covered end-to-end by the pytest suite.
10. Booking a session in the past is not blocked — the brief does not ask for it, and the
    schedule doubles as a record of what happened.
11. Sessions cannot run past midnight (nor end exactly at midnight): availability windows and
    sessions are compared as wall-clock times within a single day. The centre closes at 8pm,
    so this is theoretical.

## 5. Credentials, configuration and environment

- Demo logins: `deb`, `helen` (administrators), `tomas` (tutor); password `redgum123`
  (illustrative only, never real).
- Configuration lives in environment variables with development defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `REDGUM_SECRET_KEY` | `dev-secret-change-me` | Session cookie signing key — must be set for any real use |
| `REDGUM_DATABASE_URL` | `sqlite:///./redgum.db` | Database location |
| `REDGUM_COOKIE_SECURE` | unset (off) | Set to `1` or `true` to add the `Secure` flag to the session cookie (HTTPS deployments) |

- Sample `.env`-style values (illustrative):

```bash
export REDGUM_SECRET_KEY="change-me-to-a-long-random-string"
export REDGUM_DATABASE_URL="sqlite:///./redgum.db"
# export REDGUM_COOKIE_SECURE="true"   # only when serving over HTTPS
```

- Sample data: seven students, four tutors (one deactivated), their availability windows, the
  case study's diary week with attended, missed and cancelled sessions, and next week's booked
  sessions generated relative to today.

## 6. Recommended next-sprint backlog

In priority order:

1. **Term unavailability** — mark a tutor away for specific dates (Tomás week 8); without it
   the centre must edit windows and remember to change them back.
2. **Overlap detection** — refuse two sessions for the same tutor or student at the same time.
3. **Room allocation and clash detection** — Deb's quarter-hour room turnaround is currently
   managed by hand.
4. **Printable tutor week** — one page per tutor for the week, replacing Deb's photocopied diary.
5. **Invoices and prepaid packs** — two days a month of Deb's time.
6. **SMS reminders** — the night-before reminder Helen keeps asking for.
7. **Attendance and cancellation policy support** — record whether a cancellation was in time
   and whether it is chargeable (the diary's C vs CL distinction).
8. **Audit trail** — who moved or cancelled a session.
9. **Weekly session cap** — warn when a tutor is booked past their stated maximum.
10. **"Not booked in three weeks" report** — Helen's money-walking-out-the-door list.
