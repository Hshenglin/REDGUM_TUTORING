# Redgum Tutoring — Scheduling and Session Tracking

ISYS3001 Managing Software Development · Case Study 3.

A small web application for an after-school tutoring centre: students, tutors and their
availability, sessions, and the centre's day and week schedule. FastAPI + Jinja2 with a
SQLite database — nothing else to install.

## Prerequisites

- Python 3.10 or newer
- Optional: Docker and Docker Compose, for the containerised run

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://localhost:8000>. The SQLite database `redgum.db` is created and seeded on
first start (delete the file to reset it).

## Run with Docker

```bash
docker compose up --build
```

Open <http://localhost:8000>. The database is stored in the named volume `redgum-data`, so
data survives container restarts. To run the image without Compose:

```bash
docker build -t redgum-tutoring .
docker run -p 8000:8000 redgum-tutoring
```

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

The suite (110 tests) covers the records, the availability rule, sessions, the schedule and
the tutor view. It is also run automatically by GitHub Actions on every push and pull
request (see `.github/workflows/ci.yml`).

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
docs/
  design-spec.md          design document
  implementation-plan.md  implementation plan
  handover.md             sprint handover document
  jira-import.csv         product backlog for the Jira import
  evidence/               captured repository evidence (git log, branches, tags, test run)
.github/workflows/ci.yml  continuous integration — runs the test suite
CHANGELOG.md              release notes
Dockerfile                container image definition
docker-compose.yml        container run configuration (app + data volume)
.env.example              sample environment configuration
requirements.txt          Python dependencies
pytest.ini                pytest configuration
```

## Configuration

Environment variables (all optional, sensible defaults for local use). Copy `.env.example`
to `.env` to set them locally; the `.env` file itself is not committed.

| Variable                | Default                        | Purpose                                                    |
|-------------------------|--------------------------------|------------------------------------------------------------|
| `REDGUM_SECRET_KEY`     | `dev-secret-change-me`         | Session cookie signing key                                 |
| `REDGUM_DATABASE_URL`   | `sqlite:///./redgum.db`        | SQLAlchemy database URL                                    |
| `REDGUM_COOKIE_SECURE`  | unset (off)                    | Set to `1` or `true` to add the `Secure` flag to the cookie (HTTPS) |

## Deployment and continuous integration

- The application is containerised (`Dockerfile` and `docker-compose.yml`) and runs from a
  clean checkout by following the steps above.
- GitHub Actions (`.github/workflows/ci.yml`) installs the dependencies and runs `pytest` on
  every push and pull request.
- Releases are tagged (`v0.1.0`, `v0.2.0`); notable changes are recorded in `CHANGELOG.md`.

## Development workflow

- **Branching** — one short-lived branch per unit of work, named for its type:
  `story/NN-name` for the development stories, `group-a/...` for the enhancement work, and
  `chore/...` or `docs/...` for maintenance.
- **Commits** follow Conventional Commits — `feat(scope):`, `test(scope):`, `docs(scope):`,
  `build(...)`, `ci:`, `chore(...)` — so the history is self-documenting.
- **Integration** — each branch is merged into `main` through a pull request, using a
  no-fast-forward merge so that every unit of work keeps a traceable merge commit.
- **Releases** are tagged (`v0.1.0`, `v0.2.0`).

## More documentation

- Design spec: `docs/design-spec.md`
- Implementation plan: `docs/implementation-plan.md`
- Handover document: `docs/handover.md`
- Backlog for Jira import: `docs/jira-import.csv`
- Repository evidence: `docs/evidence/`
