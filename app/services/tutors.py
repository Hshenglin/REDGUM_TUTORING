from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession, selectinload

from app.models import Tutor


def list_tutors(db: OrmSession, q: str = "", status: str = "") -> list[Tutor]:
    stmt = select(Tutor).options(selectinload(Tutor.windows))
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(Tutor.name.ilike(like))
    if status in ("ACTIVE", "INACTIVE"):
        stmt = stmt.where(Tutor.status == status)
    return list(db.scalars(stmt.order_by(Tutor.name)))


def bookable_tutors(db: OrmSession) -> list[Tutor]:
    return list(db.scalars(select(Tutor).where(Tutor.status == "ACTIVE").order_by(Tutor.name)))


def validate_tutor_form(name: str, phone: str, subjects: str) -> tuple[dict, list[str]]:
    data: dict = {}
    errors: list[str] = []

    name = name.strip()
    if not name:
        errors.append("Tutor name is required.")
    data["name"] = name

    phone = phone.strip()
    data["phone"] = phone

    subjects = subjects.strip()
    if not subjects:
        errors.append("Subjects are required.")
    data["subjects"] = subjects

    return data, errors


def create_tutor(db: OrmSession, *, name: str, phone: str, subjects: str) -> Tutor:
    tutor = Tutor(name=name, phone=phone.strip() or None, subjects=subjects, status="ACTIVE")
    db.add(tutor)
    db.commit()
    return tutor


def update_tutor(db: OrmSession, tutor: Tutor, *, name: str, phone: str, subjects: str) -> Tutor:
    tutor.name = name
    tutor.phone = phone.strip() or None
    tutor.subjects = subjects
    db.commit()
    return tutor


def set_status(db: OrmSession, tutor: Tutor, status: str) -> Tutor:
    tutor.status = status
    db.commit()
    return tutor
