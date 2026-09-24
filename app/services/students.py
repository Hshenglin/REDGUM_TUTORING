from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.models import Student


def list_students(db: OrmSession, q: str = "", status: str = "") -> list[Student]:
    stmt = select(Student)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(Student.name.ilike(like))
    if status in ("ACTIVE", "INACTIVE"):
        stmt = stmt.where(Student.status == status)
    return list(db.scalars(stmt.order_by(Student.name)))


def validate_student_form(name: str, year_level: str, school: str, contact_name: str,
                          contact_phone: str, contact_email: str, subjects: str) -> tuple[dict, list[str]]:
    data: dict = {}
    errors: list[str] = []

    name = name.strip()
    if not name:
        errors.append("Student name is required.")
    data["name"] = name

    year_level = year_level.strip()
    if not year_level:
        errors.append("Year level is required.")
    else:
        try:
            year = int(year_level)
        except ValueError:
            errors.append("Year level must be a whole number between 5 and 12.")
        else:
            if not 5 <= year <= 12:
                errors.append("Year level must be between 5 and 12.")
            else:
                data["year_level"] = year

    school = school.strip()
    data["school"] = school

    contact_name = contact_name.strip()
    if not contact_name:
        errors.append("Family contact name is required.")
    data["contact_name"] = contact_name

    contact_phone = contact_phone.strip()
    if not contact_phone:
        errors.append("Family contact phone is required.")
    data["contact_phone"] = contact_phone

    contact_email = contact_email.strip()
    data["contact_email"] = contact_email

    subjects = subjects.strip()
    data["subjects"] = subjects

    return data, errors


def create_student(db: OrmSession, *, name: str, year_level: int, school: str, contact_name: str,
                   contact_phone: str, contact_email: str, subjects: str) -> Student:
    student = Student(name=name, year_level=year_level, school=school.strip() or None,
                      contact_name=contact_name, contact_phone=contact_phone,
                      contact_email=contact_email.strip() or None,
                      subjects=subjects.strip() or None, status="ACTIVE")
    db.add(student)
    db.commit()
    return student


def update_student(db: OrmSession, student: Student, *, name: str, year_level: int, school: str,
                   contact_name: str, contact_phone: str, contact_email: str, subjects: str) -> Student:
    student.name = name
    student.year_level = year_level
    student.school = school.strip() or None
    student.contact_name = contact_name
    student.contact_phone = contact_phone
    student.contact_email = contact_email.strip() or None
    student.subjects = subjects.strip() or None
    db.commit()
    return student


def set_status(db: OrmSession, student: Student, status: str) -> Student:
    student.status = status
    db.commit()
    return student
