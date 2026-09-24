from sqlalchemy import inspect

from app.models import Student


def test_tables_are_created(db_session):
    tables = set(inspect(db_session.get_bind()).get_table_names())
    assert {"student", "tutor", "availability_window", "session", "app_user"} <= tables


def test_student_round_trip(db_session):
    student = Student(name="Ella Nguyen", year_level=11, contact_name="Mai Nguyen", contact_phone="0412 660 118")
    db_session.add(student)
    db_session.commit()
    db_session.expire_all()

    loaded = db_session.get(Student, student.id)
    assert loaded.name == "Ella Nguyen"
    assert loaded.year_level == 11
    assert loaded.status == "ACTIVE"
    assert loaded.created_at is not None


def test_unknown_path_returns_404(client):
    assert client.get("/no-such-page").status_code == 404
