from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

DAY_NAMES = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")
OPEN_DAYS = ("TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY")
DAY_ORDER = {day: index for index, day in enumerate(OPEN_DAYS)}
SESSION_LENGTHS = (60, 90)
SESSION_STATUSES = ("BOOKED", "ATTENDED", "CANCELLED", "MISSED")


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Student(Base):
    __tablename__ = "student"
    __table_args__ = (CheckConstraint("year_level BETWEEN 5 AND 12", name="ck_student_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    year_level: Mapped[int]
    school: Mapped[str | None] = mapped_column(String(120))
    contact_name: Mapped[str] = mapped_column(String(100))
    contact_phone: Mapped[str] = mapped_column(String(20))
    contact_email: Mapped[str | None] = mapped_column(String(120))
    subjects: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Tutor(Base):
    __tablename__ = "tutor"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    subjects: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    windows: Mapped[list[AvailabilityWindow]] = relationship(
        back_populates="tutor", cascade="all, delete-orphan"
    )


class AvailabilityWindow(Base):
    __tablename__ = "availability_window"
    __table_args__ = (UniqueConstraint("tutor_id", "day_of_week", "start_time", "end_time", name="uq_window"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutor.id"))
    day_of_week: Mapped[str] = mapped_column(String(10))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    tutor: Mapped[Tutor] = relationship(back_populates="windows")


class Session(Base):
    __tablename__ = "session"
    __table_args__ = (Index("ix_session_tutor_date", "tutor_id", "session_date"), Index("ix_session_student", "student_id"), CheckConstraint("length_minutes IN (60, 90)", name="ck_session_length"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutor.id"))
    subject: Mapped[str] = mapped_column(String(100))
    session_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    length_minutes: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default="BOOKED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    student: Mapped[Student] = relationship()
    tutor: Mapped[Tutor] = relationship()


class AppUser(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))
    tutor_id: Mapped[int | None] = mapped_column(ForeignKey("tutor.id"))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    tutor: Mapped[Tutor | None] = relationship()
