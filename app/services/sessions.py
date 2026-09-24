from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession, selectinload

from app.errors import DomainError
from app.formatting import fmt_time
from app.models import DAY_NAMES, SESSION_LENGTHS, SESSION_STATUSES, Session, Student, Tutor
from app.validation import parse_date, parse_time


def validate_slot(tutor: Tutor, session_date: date, start_time: time, length_minutes: int) -> None:
    """The centre's operating rule: a session must fit entirely inside one availability window."""
    if length_minutes not in SESSION_LENGTHS:
        raise DomainError("Sessions are 60 or 90 minutes long.")
    if tutor.status != "ACTIVE":
        raise DomainError(f"{tutor.name} is not an active tutor.")
    day = DAY_NAMES[session_date.weekday()]
    windows = [w for w in tutor.windows if w.day_of_week == day]
    if not windows:
        raise DomainError(f"{tutor.name} has no availability on {day.title()}.")
    end_moment = datetime.combine(session_date, start_time) + timedelta(minutes=length_minutes)
    if end_moment.date() != session_date:
        raise DomainError(
            f"A {length_minutes}-minute session starting at {fmt_time(start_time)} would run past midnight.")
    end_time = end_moment.time()
    for window in windows:
        if window.start_time <= start_time and end_time <= window.end_time:
            return
    listed = ", ".join(f"{fmt_time(w.start_time)}–{fmt_time(w.end_time)}"
                       for w in sorted(windows, key=lambda w: w.start_time))
    raise DomainError(
        f"{tutor.name} is only available on {day.title()} {listed}; "
        f"a {length_minutes}-minute session starting at {fmt_time(start_time)} would not fit."
    )


def validate_session_form(db: OrmSession, student_id: str, tutor_id: str, subject: str,
                          session_date: str, start_time: str,
                          length_minutes: str) -> tuple[dict, list[str]]:
    data: dict = {}
    errors: list[str] = []

    student = db.get(Student, int(student_id)) if student_id.isdigit() else None
    if student is None:
        errors.append("Choose a student.")
    else:
        data["student"] = student

    tutor = db.get(Tutor, int(tutor_id)) if tutor_id.isdigit() else None
    if tutor is None:
        errors.append("Choose a tutor.")
    else:
        data["tutor"] = tutor

    subject = subject.strip()
    if not subject:
        errors.append("Subject is required.")
    elif len(subject) > 100:
        errors.append("Subject must be 100 characters or fewer.")
    data["subject"] = subject

    parsed_date = parse_date(session_date)
    if parsed_date is None:
        errors.append("Date must look like 2026-08-11.")
    else:
        data["session_date"] = parsed_date

    parsed_start = parse_time(start_time)
    if parsed_start is None:
        errors.append("Start time must look like 15:30.")
    else:
        data["start_time"] = parsed_start

    length = int(length_minutes) if length_minutes.isdigit() else None
    if length not in SESSION_LENGTHS:
        errors.append("Length must be 60 or 90 minutes.")
    else:
        data["length_minutes"] = length

    return data, errors


def book_session(db: OrmSession, *, student: Student, tutor: Tutor, subject: str, session_date: date,
                 start_time: time, length_minutes: int) -> Session:
    if student.status != "ACTIVE":
        raise DomainError(f"{student.name} is not an active student.")
    validate_slot(tutor, session_date, start_time, length_minutes)
    session = Session(student_id=student.id, tutor_id=tutor.id, subject=subject,
                      session_date=session_date, start_time=start_time,
                      length_minutes=length_minutes, status="BOOKED")
    db.add(session)
    db.commit()
    return session


def list_sessions(db: OrmSession, *, date_from: date | None = None, date_to: date | None = None,
                  tutor_id: int | None = None, student_id: int | None = None,
                  status: str = "") -> list[Session]:
    stmt = select(Session).options(selectinload(Session.student), selectinload(Session.tutor))
    if date_from is not None:
        stmt = stmt.where(Session.session_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Session.session_date <= date_to)
    if tutor_id is not None:
        stmt = stmt.where(Session.tutor_id == tutor_id)
    if student_id is not None:
        stmt = stmt.where(Session.student_id == student_id)
    if status in SESSION_STATUSES:
        stmt = stmt.where(Session.status == status)
    return list(db.scalars(stmt.order_by(Session.session_date, Session.start_time)))
