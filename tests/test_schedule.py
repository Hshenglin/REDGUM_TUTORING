from datetime import date, time, timedelta


def test_day_view_shows_only_that_day(admin_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2026, 8, 11), start_time=time(15, 30))
    make_session(student, tutor_record, session_date=date(2026, 8, 13), start_time=time(16, 0))

    r = admin_client.get("/schedule?view=day&date=2026-08-11")
    assert r.status_code == 200
    assert "Tue 11 Aug 2026" in r.text
    assert "Thu 13 Aug 2026" not in r.text


def test_week_view_covers_tuesday_to_saturday(admin_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2026, 8, 15), start_time=time(9, 0))

    r = admin_client.get("/schedule?view=week&date=2026-08-13")
    assert r.status_code == 200
    for label in ["Tue 11 Aug 2026", "Wed 12 Aug 2026", "Thu 13 Aug 2026",
                  "Fri 14 Aug 2026", "Sat 15 Aug 2026"]:
        assert label in r.text
    assert "Ella Nguyen" in r.text


def test_empty_day_shows_a_clear_message(admin_client):
    r = admin_client.get("/schedule?view=day&date=2026-08-11")
    assert r.status_code == 200
    assert "No sessions." in r.text


def test_student_history_lists_past_and_future(admin_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2026, 8, 11), start_time=time(15, 30), status="ATTENDED")
    make_session(student, tutor_record, session_date=date.today() + timedelta(days=7), start_time=time(15, 30))

    r = admin_client.get(f"/students/{student.id}/sessions")
    assert r.status_code == 200
    assert "Upcoming" in r.text
    assert "Past" in r.text
    assert "Tue 11 Aug 2026" in r.text
    assert "No upcoming sessions." not in r.text


def test_tutor_cannot_see_the_schedule(tutor_client):
    assert tutor_client.get("/schedule").status_code == 403
