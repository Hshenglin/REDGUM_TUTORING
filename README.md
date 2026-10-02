# Redgum Tutoring — Scheduling and Session Tracking

ISYS3001 Managing Software Development · Case Study 3.

A small web application for an after-school tutoring centre: students, tutors and their
availability, sessions, and the centre's day and week schedule. FastAPI + Jinja2 with a
SQLite database — nothing else to install.

## Prerequisites

- Python 3.10 or newer

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://localhost:8000>. The SQLite database `redgum.db` is created and seeded on
first start (delete the file to reset it).

## Demo accounts

Password for all demo accounts: `redgum123` (illustrative values only).

| Username | Role                        |
|----------|-----------------------------|
| deb      | Administrator               |
| helen    | Administrator (also a tutor)|
| tomas    | Tutor                       |

## Running the tests

```bash
pytest
```

## What the system does

- **Students** — add, find, edit and deactivate students with their year level, school and
  family contact.
- **Tutors** — add, edit and deactivate tutors with the subjects they teach.
- **Availability** — record each tutor's availability windows (day, start, end). A tutor can
  have several windows on several days.
- **Sessions** — book a student with a tutor, move it, cancel it, or mark it attended or
  missed. The centre's operating rule is enforced: **a session must fit entirely inside one
  of that tutor's availability windows for that day**, and the system says why when it does
  not.
- **Schedule** — the centre sees a day or a week at a glance and can filter by tutor; a
  student's past and future sessions are listed on their page.
- **Tutor view** — a tutor sees only their own upcoming sessions.

## Project layout

```
app/
  main.py          FastAPI application (middleware, error pages, routers, startup)
  db.py            engine, session factory, get_db, init_db
  models.py        Student, Tutor, AvailabilityWindow, Session, AppUser
  security.py      password hashing, login dependencies, role guard
  services/        students, tutors, availability, sessions (the availability rule), schedule
  routers/         auth, students, tutors, availability, sessions, views
  templates/       Jinja2 templates
  static/style.css single stylesheet (no CDN)
tests/             pytest suite
docs/              design spec, implementation plan, handover, Jira backlog
```

## Configuration

Environment variables (all optional, sensible defaults for local use):

| Variable                | Default                        | Purpose                                                    |
|-------------------------|--------------------------------|------------------------------------------------------------|
| `REDGUM_SECRET_KEY`     | `dev-secret-change-me`         | Session cookie signing key                                 |
| `REDGUM_DATABASE_URL`   | `sqlite:///./redgum.db`        | SQLAlchemy database URL                                    |
| `REDGUM_COOKIE_SECURE`  | unset (off)                    | Set to `1` or `true` to add the `Secure` flag to the cookie (HTTPS) |

## More documentation

- Design spec: `docs/superpowers/specs/2026-09-24-redgum-tutoring-design.md`
- Handover document: `docs/handover.md`
- Backlog for Jira import: `docs/jira-import.csv`
