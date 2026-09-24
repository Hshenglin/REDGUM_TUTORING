from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.models import Session


def week_start(value: date) -> date:
    """Tuesday of the centre week that contains the given date."""
    return value - timedelta(days=(value.weekday() - 1) % 7)


def sessions_between(db: OrmSession, start: date, end: date,
                     tutor_id: int | None = None) -> list[Session]:
    stmt = select(Session).where(Session.session_date >= start, Session.session_date <= end)
    if tutor_id is not None:
        stmt = stmt.where(Session.tutor_id == tutor_id)
    return list(db.scalars(stmt.order_by(Session.session_date, Session.start_time)))


def week_days(week_start_date: date) -> list[date]:
    """Tuesday to Saturday."""
    return [week_start_date + timedelta(days=offset) for offset in range(5)]


def sessions_on(sessions: list[Session], day: date) -> list[Session]:
    return [s for s in sessions if s.session_date == day]


def student_sessions(db: OrmSession, student_id: int, today: date) -> tuple[list[Session], list[Session]]:
    sessions = list(db.scalars(select(Session)
                               .where(Session.student_id == student_id)
                               .order_by(Session.session_date, Session.start_time)))
    past = [s for s in sessions if s.session_date < today]
    future = [s for s in sessions if s.session_date >= today]
    return past, future


def upcoming_for_tutor(db: OrmSession, tutor_id: int, today: date) -> list[Session]:
    return list(db.scalars(select(Session)
                           .where(Session.tutor_id == tutor_id,
                                  Session.session_date >= today,
                                  Session.status == "BOOKED")
                           .order_by(Session.session_date, Session.start_time)))
