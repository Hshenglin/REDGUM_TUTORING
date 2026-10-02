from datetime import time

from app.models import AvailabilityWindow


def test_availability_page_lists_windows(admin_client, tutor_record):
    r = admin_client.get(f"/tutors/{tutor_record.id}/availability")
    assert r.status_code == 200
    assert "Tuesday" in r.text
    assert "3:30 pm" in r.text
    assert "7:00 pm" in r.text


def test_add_window(admin_client, tutor_record, db_session):
    r = admin_client.post(f"/tutors/{tutor_record.id}/availability", data={
        "day_of_week": "WEDNESDAY", "start_time": "15:30", "end_time": "18:00",
    }, follow_redirects=False)
    assert r.status_code == 303
    window = db_session.query(AvailabilityWindow).filter_by(
        tutor_id=tutor_record.id, day_of_week="WEDNESDAY").one()
    assert window.start_time == time(15, 30)
    assert window.end_time == time(18, 0)


def test_end_before_start_is_rejected(admin_client, tutor_record, db_session):
    before = db_session.query(AvailabilityWindow).count()
    r = admin_client.post(f"/tutors/{tutor_record.id}/availability", data={
        "day_of_week": "WEDNESDAY", "start_time": "18:00", "end_time": "15:30",
    })
    assert r.status_code == 400
    assert "End time must be after the start time." in r.text
    assert db_session.query(AvailabilityWindow).count() == before


def test_invalid_day_and_time_are_rejected(admin_client, tutor_record):
    r = admin_client.post(f"/tutors/{tutor_record.id}/availability", data={
        "day_of_week": "MONDAY", "start_time": "nonsense", "end_time": "18:00",
    })
    assert r.status_code == 400
    assert "Day must be one of Tuesday to Saturday." in r.text
    assert "Start time must look like 15:30." in r.text


def test_delete_window(admin_client, tutor_record, db_session):
    window = tutor_record.windows[0]
    r = admin_client.post(f"/availability/{window.id}/delete", follow_redirects=False)
    assert r.status_code == 303
    assert db_session.get(AvailabilityWindow, window.id) is None


def test_tutor_cannot_manage_availability(tutor_client, tutor_record):
    assert tutor_client.get(f"/tutors/{tutor_record.id}/availability").status_code == 403


def test_unknown_tutor_returns_404(admin_client):
    assert admin_client.get("/tutors/9999/availability").status_code == 404


def test_unknown_window_delete_returns_404(admin_client):
    assert admin_client.post("/availability/9999/delete").status_code == 404


def test_day_input_is_case_insensitive(admin_client, tutor_record, db_session):
    r = admin_client.post(f"/tutors/{tutor_record.id}/availability", data={
        "day_of_week": " wednesday ", "start_time": "15:30", "end_time": "17:00",
    }, follow_redirects=False)
    assert r.status_code == 303
    assert db_session.query(AvailabilityWindow).filter_by(
        tutor_id=tutor_record.id, day_of_week="WEDNESDAY").count() == 1


def test_equal_start_and_end_is_rejected(admin_client, tutor_record, db_session):
    before = db_session.query(AvailabilityWindow).count()
    r = admin_client.post(f"/tutors/{tutor_record.id}/availability", data={
        "day_of_week": "WEDNESDAY", "start_time": "16:00", "end_time": "16:00",
    })
    assert r.status_code == 400
    assert "End time must be after the start time." in r.text
    assert db_session.query(AvailabilityWindow).count() == before


def test_windows_are_listed_in_week_order(admin_client, tutor_record):
    text = admin_client.get(f"/tutors/{tutor_record.id}/availability").text
    assert text.index("<td>Tuesday</td>") < text.index("<td>Thursday</td>") < text.index("<td>Saturday</td>")


def test_each_window_row_links_to_its_edit_page(admin_client, tutor_record):
    window = tutor_record.windows[0]
    text = admin_client.get(f"/tutors/{tutor_record.id}/availability").text
    assert f'href="/availability/{window.id}/edit"' in text


def test_edit_page_prefills_the_stored_window(admin_client, tutor_record):
    window = tutor_record.windows[0]
    r = admin_client.get(f"/availability/{window.id}/edit")
    assert r.status_code == 200
    assert f'action="/availability/{window.id}/edit"' in r.text
    assert 'value="15:30"' in r.text
    assert 'value="19:00"' in r.text


def test_edit_window(admin_client, tutor_record, db_session):
    window = tutor_record.windows[0]
    r = admin_client.post(f"/availability/{window.id}/edit", data={
        "day_of_week": "TUESDAY", "start_time": "16:00", "end_time": "19:00",
    }, follow_redirects=False)
    assert r.status_code == 303
    db_session.refresh(window)
    assert window.start_time == time(16, 0)


def test_invalid_edit_keeps_the_stored_window(admin_client, tutor_record, db_session):
    window = tutor_record.windows[0]
    r = admin_client.post(f"/availability/{window.id}/edit", data={
        "day_of_week": "MONDAY", "start_time": "16:00", "end_time": "15:00",
    })
    assert r.status_code == 400
    assert "Day must be one of Tuesday to Saturday." in r.text
    assert "End time must be after the start time." in r.text
    db_session.refresh(window)
    assert window.day_of_week == "TUESDAY"
    assert window.start_time == time(15, 30)


def test_unknown_window_edit_returns_404(admin_client):
    assert admin_client.get("/availability/9999/edit").status_code == 404
    assert admin_client.post("/availability/9999/edit", data={
        "day_of_week": "TUESDAY", "start_time": "15:30", "end_time": "18:00",
    }).status_code == 404
