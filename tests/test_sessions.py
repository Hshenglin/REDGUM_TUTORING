from datetime import date, time

from app.models import Session


def test_book_a_session_inside_availability(admin_client, tutor_record, make_student, db_session):
    student = make_student()
    r = admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "Physics",
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    }, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/sessions"
    session = db_session.query(Session).one()
    assert session.status == "BOOKED"
    assert session.start_time == time(16, 0)


def test_booking_outside_availability_is_refused(admin_client, tutor_record, make_student, db_session):
    student = make_student()
    r = admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "Physics",
        "session_date": "2026-08-11", "start_time": "18:30", "length_minutes": "60",
    })
    assert r.status_code == 400
    assert "would not fit" in r.text
    assert db_session.query(Session).count() == 0


def test_deactivated_tutor_is_not_offered_and_cannot_be_booked(admin_client, tutor_record, make_student, db_session):
    tutor_record.status = "INACTIVE"
    db_session.commit()
    student = make_student()

    form = admin_client.get("/sessions/new")
    assert "Tomás Ferreira" not in form.text

    r = admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "Physics",
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    })
    assert r.status_code == 400
    assert "not an active tutor" in r.text


def test_inactive_student_cannot_be_booked(admin_client, tutor_record, make_student):
    student = make_student(status="INACTIVE")
    r = admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "Physics",
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    })
    assert r.status_code == 400
    assert "not an active student" in r.text


def test_required_fields_are_reported(admin_client, db_session):
    r = admin_client.post("/sessions/new", data={
        "student_id": "", "tutor_id": "", "subject": "", "session_date": "", "start_time": "",
        "length_minutes": "45",
    })
    assert r.status_code == 400
    assert "Choose a student." in r.text
    assert "Choose a tutor." in r.text
    assert "Subject is required." in r.text
    assert "Date must look like 2026-08-11." in r.text
    assert "Start time must look like 15:30." in r.text
    assert "Length must be 60 or 90 minutes." in r.text
    assert db_session.query(Session).count() == 0


def test_subject_longer_than_100_characters_is_rejected(admin_client, tutor_record, make_student, db_session):
    student = make_student()
    r = admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "x" * 101,
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    })
    assert r.status_code == 400
    assert "Subject must be 100 characters or fewer." in r.text
    assert db_session.query(Session).count() == 0


def test_booked_session_appears_in_the_list(admin_client, tutor_record, make_student):
    student = make_student()
    admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "Quantum Mechanics",
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    })
    r = admin_client.get("/sessions")
    assert "Quantum Mechanics" in r.text
    assert "4:00 pm" in r.text
    assert "60 min" in r.text
    assert "No sessions match." not in r.text


def test_list_filters_by_tutor_student_date_and_status(admin_client, tutor_record, make_student, make_session, db_session):
    ella = make_student(name="Ella Nguyen")
    kai = make_student(name="Kai Lombardo")
    make_session(ella, tutor_record, session_date=date(2026, 8, 11), start_time=time(15, 30),
                 subject="Physics")
    make_session(kai, tutor_record, session_date=date(2026, 8, 13), start_time=time(16, 0),
                 subject="Chemistry", status="CANCELLED")

    r = admin_client.get("/sessions?tutor_id=%d" % tutor_record.id)
    assert "Physics" in r.text and "Chemistry" in r.text

    r = admin_client.get("/sessions?student_id=%d" % ella.id)
    assert "Physics" in r.text and "Chemistry" not in r.text

    r = admin_client.get("/sessions?date_from=2026-08-12&date_to=2026-08-14")
    assert "Chemistry" in r.text and "Physics" not in r.text

    r = admin_client.get("/sessions?status=CANCELLED")
    assert "Chemistry" in r.text and "Physics" not in r.text


def test_malformed_filters_are_ignored_rather_than_erroring(admin_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, subject="Physics")

    r = admin_client.get("/sessions?date_from=garbage&date_to=2026-99-99&tutor_id=abc&student_id=-1&status=BOGUS")
    assert r.status_code == 200
    assert "Physics" in r.text


def test_inactive_students_sessions_are_still_listed(admin_client, tutor_record, make_student, make_session, db_session):
    student = make_student(status="INACTIVE")
    make_session(student, tutor_record, subject="Legacy Physics")

    r = admin_client.get("/sessions")
    assert "Legacy Physics" in r.text


def test_tutor_cannot_book_sessions(tutor_client):
    assert tutor_client.get("/sessions").status_code == 403
    assert tutor_client.get("/sessions/new").status_code == 403


def test_move_a_session_within_availability(admin_client, tutor_record, make_student, make_session, db_session):
    session = make_session(make_student(), tutor_record, session_date=date(2026, 8, 11), start_time=time(15, 30))
    r = admin_client.post(f"/sessions/{session.id}/edit", data={
        "session_date": "2026-08-11", "start_time": "17:00", "length_minutes": "60",
    }, follow_redirects=False)
    assert r.status_code == 303
    db_session.refresh(session)
    assert session.start_time == time(17, 0)


def test_move_outside_availability_is_refused_and_nothing_changes(admin_client, tutor_record, make_student, make_session, db_session):
    session = make_session(make_student(), tutor_record, session_date=date(2026, 8, 11), start_time=time(15, 30))
    r = admin_client.post(f"/sessions/{session.id}/edit", data={
        "session_date": "2026-08-11", "start_time": "18:30", "length_minutes": "60",
    })
    assert r.status_code == 400
    assert "would not fit" in r.text
    db_session.refresh(session)
    assert session.start_time == time(15, 30)


def test_cancel_a_session_keeps_it_visible(admin_client, tutor_record, make_student, make_session, db_session):
    session = make_session(make_student(), tutor_record)
    r = admin_client.post(f"/sessions/{session.id}/cancel", follow_redirects=False)
    assert r.status_code == 303
    db_session.refresh(session)
    assert session.status == "CANCELLED"
    listing = admin_client.get("/sessions")
    assert "Cancelled" in listing.text


def test_mark_attended_and_missed(admin_client, tutor_record, make_student, make_session, db_session):
    attended = make_session(make_student(), tutor_record, start_time=time(15, 30))
    missed = make_session(make_student(name="Kai Lombardo"), tutor_record, start_time=time(16, 30))

    admin_client.post(f"/sessions/{attended.id}/status", data={"outcome": "ATTENDED"})
    admin_client.post(f"/sessions/{missed.id}/status", data={"outcome": "MISSED"})

    db_session.refresh(attended)
    db_session.refresh(missed)
    assert attended.status == "ATTENDED"
    assert missed.status == "MISSED"


def test_a_finished_session_cannot_be_moved_or_cancelled(admin_client, tutor_record, make_student, make_session):
    session = make_session(make_student(), tutor_record, status="CANCELLED")
    moved = admin_client.post(f"/sessions/{session.id}/edit", data={
        "session_date": "2026-08-11", "start_time": "17:00", "length_minutes": "60",
    })
    assert moved.status_code == 400
    assert "Only booked sessions can be moved." in moved.text
    cancelled = admin_client.post(f"/sessions/{session.id}/cancel", follow_redirects=False)
    assert cancelled.status_code == 303
    listing = admin_client.get("/sessions")
    assert "Only booked sessions can be cancelled." in listing.text


def test_moving_one_session_does_not_affect_another(admin_client, tutor_record, make_student, make_session, db_session):
    student = make_student()
    first = make_session(student, tutor_record, start_time=time(15, 30))
    second = make_session(student, tutor_record, start_time=time(17, 0))

    admin_client.post(f"/sessions/{first.id}/edit", data={
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    })

    db_session.refresh(first)
    db_session.refresh(second)
    assert first.start_time == time(16, 0)
    assert second.start_time == time(17, 0)


def test_tutor_cannot_change_sessions(tutor_client, tutor_record, make_student, make_session):
    session = make_session(make_student(), tutor_record)
    assert tutor_client.post(f"/sessions/{session.id}/cancel").status_code == 403
    assert tutor_client.get(f"/sessions/{session.id}/edit").status_code == 403
