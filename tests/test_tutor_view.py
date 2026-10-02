from datetime import date, time

from app.models import Tutor


def test_tutor_sees_own_upcoming_sessions(tutor_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2099, 1, 5), start_time=time(16, 0), subject="Physics")

    r = tutor_client.get("/my-sessions")
    assert r.status_code == 200
    assert "Ella Nguyen" in r.text
    assert "Physics" in r.text


def test_tutor_does_not_see_another_tutors_sessions(tutor_client, db_session, make_student, make_session):
    other = Tutor(name="Priyanka Shah", subjects="Maths 5-10", status="ACTIVE")
    db_session.add(other)
    db_session.commit()
    student = make_student()
    make_session(student, other, session_date=date(2099, 1, 5), start_time=time(16, 0), subject="Maths")

    r = tutor_client.get("/my-sessions")
    assert r.status_code == 200
    assert "Priyanka Shah" not in r.text
    assert "No upcoming sessions." in r.text


def test_tutor_with_no_sessions_gets_an_empty_list(tutor_client):
    r = tutor_client.get("/my-sessions")
    assert r.status_code == 200
    assert "No upcoming sessions." in r.text


def test_admin_without_a_tutor_profile_gets_an_empty_list(admin_client):
    r = admin_client.get("/my-sessions")
    assert r.status_code == 200
    assert "No upcoming sessions." in r.text


def test_past_and_cancelled_sessions_are_not_upcoming(tutor_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2020, 1, 7), start_time=time(16, 0))
    make_session(student, tutor_record, session_date=date(2099, 1, 5), start_time=time(16, 0), status="CANCELLED")

    r = tutor_client.get("/my-sessions")
    assert "No upcoming sessions." in r.text


def test_anonymous_visitor_is_redirected_to_login(client):
    r = client.get("/my-sessions", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_tutor_cannot_open_admin_pages(tutor_client):
    assert tutor_client.get("/schedule").status_code == 403
    assert tutor_client.get("/students").status_code == 403
