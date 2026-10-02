# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-10-03

### Added

- Student search matches the family contact name as well as the student name.
- Length limits on the student fields: name, school, family contact name, family
  contact phone, family contact email and subjects.
- Tutor search matches the subjects as well as the tutor name.
- Length limits on the tutor fields: name, phone and subjects.
- Editing of an availability window, with a link from every row of the tutor's
  availability page.
- Rejection of duplicate availability windows on both the add and the edit path.
- Deployment configuration: a Dockerfile, a compose file, an environment template
  and a GitHub Actions pipeline.

## [0.1.0] - 2026-09-24

### Added

- Coordinator login with role separation between administrators and tutors.
- Student and tutor records with search, create, edit and deactivate.
- Weekly availability windows per tutor.
- Session booking, moving, cancelling and outcome recording, with the centre's rule
  that a session must fit inside a tutor's availability window.
- Day and week schedule, per-student session history, and the tutor's own upcoming
  sessions.
- Demo seed data, the design spec, the implementation plan, the handover document and
  the Jira backlog import, delivered as ten story branches.
