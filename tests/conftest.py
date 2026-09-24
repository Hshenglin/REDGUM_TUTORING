from datetime import date, time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import AppUser, AvailabilityWindow, Session, Student, Tutor
from app.security import hash_password

DEMO_PASSWORD = "redgum123"


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture(autouse=True)
def _clear_overrides_after_test():
    yield
    app.dependency_overrides.clear()


def _make_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture()
def client(db_session):
    c = _make_client(db_session)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin(db_session):
    user = AppUser(username="deb", password_hash=hash_password(DEMO_PASSWORD), role="ADMIN", status="ACTIVE")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def tutor_record(db_session):
    tutor = Tutor(name="Tomás Ferreira", phone="0407 512 884",
                  subjects="Physics 10-12, Chemistry 10-12", status="ACTIVE")
    tutor.windows.extend([
        AvailabilityWindow(day_of_week="TUESDAY", start_time=time(15, 30), end_time=time(19, 0)),
        AvailabilityWindow(day_of_week="THURSDAY", start_time=time(16, 0), end_time=time(18, 30)),
        AvailabilityWindow(day_of_week="SATURDAY", start_time=time(9, 0), end_time=time(12, 30)),
    ])
    db_session.add(tutor)
    db_session.commit()
    return tutor


@pytest.fixture()
def tutor_user(db_session, tutor_record):
    user = AppUser(username="tomas", password_hash=hash_password(DEMO_PASSWORD), role="TUTOR",
                   tutor_id=tutor_record.id, status="ACTIVE")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def admin_client(db_session, admin):
    c = _make_client(db_session)
    response = c.post("/login", data={"username": "deb", "password": DEMO_PASSWORD}, follow_redirects=False)
    assert response.status_code == 303
    yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def tutor_client(db_session, tutor_user):
    c = _make_client(db_session)
    response = c.post("/login", data={"username": "tomas", "password": DEMO_PASSWORD}, follow_redirects=False)
    assert response.status_code == 303
    yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def make_student(db_session):
    def _make(name="Ella Nguyen", year_level=11, status="ACTIVE", **kwargs):
        student = Student(
            name=name, year_level=year_level, school=kwargs.get("school", "Limestone High"),
            contact_name=kwargs.get("contact_name", "Mai Nguyen"),
            contact_phone=kwargs.get("contact_phone", "0412 660 118"),
            contact_email=kwargs.get("contact_email"), subjects=kwargs.get("subjects", "Physics"),
            status=status,
        )
        db_session.add(student)
        db_session.commit()
        return student
    return _make


@pytest.fixture()
def make_session(db_session):
    def _make(student, tutor, session_date=date(2026, 8, 11), start_time=time(15, 30),
              length_minutes=60, subject="Physics", status="BOOKED"):
        session = Session(
            student_id=student.id, tutor_id=tutor.id, subject=subject,
            session_date=session_date, start_time=start_time,
            length_minutes=length_minutes, status=status,
        )
        db_session.add(session)
        db_session.commit()
        return session
    return _make
