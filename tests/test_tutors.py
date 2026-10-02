from app.models import Tutor


def test_admin_sees_tutor_list(admin_client, tutor_record):
    r = admin_client.get("/tutors")
    assert r.status_code == 200
    assert "Tomás Ferreira" in r.text


def test_create_tutor(admin_client, db_session):
    r = admin_client.post("/tutors/new", data={
        "name": "Priyanka Shah", "phone": "0407 883 402",
        "subjects": "Maths 5-10, Science 7-10",
    }, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/tutors"
    tutor = db_session.query(Tutor).filter_by(name="Priyanka Shah").one()
    assert tutor.status == "ACTIVE"


def test_name_and_subjects_are_required(admin_client, db_session):
    r = admin_client.post("/tutors/new", data={"name": "", "phone": "", "subjects": ""})
    assert r.status_code == 400
    assert "Tutor name is required." in r.text
    assert "Subjects are required." in r.text
    assert db_session.query(Tutor).count() == 0


def test_edit_tutor(admin_client, tutor_record, db_session):
    r = admin_client.post(f"/tutors/{tutor_record.id}/edit", data={
        "name": "Tomás Ferreira", "phone": "0407 512 884",
        "subjects": "Physics 10-12, Chemistry 10-12, Maths Methods 11-12",
    }, follow_redirects=False)
    assert r.status_code == 303
    db_session.refresh(tutor_record)
    assert "Maths Methods" in tutor_record.subjects


def test_deactivate_tutor_keeps_sessions(admin_client, tutor_record, make_student, make_session, db_session):
    session = make_session(make_student(), tutor_record)
    admin_client.post(f"/tutors/{tutor_record.id}/status", data={"status": "INACTIVE"})
    db_session.refresh(tutor_record)
    assert tutor_record.status == "INACTIVE"
    db_session.refresh(session)
    assert session.status == "BOOKED"
    assert session.tutor_id == tutor_record.id


def test_tutor_cannot_access_tutor_admin(tutor_client):
    assert tutor_client.get("/tutors").status_code == 403


def test_unknown_tutor_edit_returns_404(admin_client):
    assert admin_client.get("/tutors/9999/edit").status_code == 404


def test_invalid_status_is_rejected(admin_client, tutor_record, db_session):
    r = admin_client.post(f"/tutors/{tutor_record.id}/status", data={"status": "DELETED"})
    assert r.status_code == 400
    assert "Invalid status" in r.text
    db_session.refresh(tutor_record)
    assert tutor_record.status == "ACTIVE"


def test_status_and_edit_on_unknown_tutor_return_404(admin_client):
    assert admin_client.post("/tutors/9999/edit", data={
        "name": "X", "phone": "", "subjects": "Y",
    }).status_code == 404
    assert admin_client.post("/tutors/9999/status", data={"status": "INACTIVE"}).status_code == 404
    assert admin_client.post("/tutors/9999/status", data={"status": "BOGUS"}).status_code == 404


def test_edit_validation_failure_keeps_the_record(admin_client, tutor_record, db_session):
    r = admin_client.post(f"/tutors/{tutor_record.id}/edit", data={
        "name": "", "phone": "0407 512 884", "subjects": "",
    })
    assert r.status_code == 400
    assert "Tutor name is required." in r.text
    assert "Subjects are required." in r.text
    assert f'action="/tutors/{tutor_record.id}/edit"' in r.text
    db_session.refresh(tutor_record)
    assert tutor_record.name == "Tomás Ferreira"
    assert "Physics" in tutor_record.subjects


def test_whitespace_only_name_and_subjects_are_rejected(admin_client, db_session):
    r = admin_client.post("/tutors/new", data={"name": "   ", "phone": "", "subjects": "  "})
    assert r.status_code == 400
    assert "Tutor name is required." in r.text
    assert "Subjects are required." in r.text
    assert db_session.query(Tutor).count() == 0


def test_reactivate_tutor(admin_client, tutor_record, db_session):
    admin_client.post(f"/tutors/{tutor_record.id}/status", data={"status": "INACTIVE"})
    db_session.refresh(tutor_record)
    assert tutor_record.status == "INACTIVE"
    admin_client.post(f"/tutors/{tutor_record.id}/status", data={"status": "ACTIVE"})
    db_session.refresh(tutor_record)
    assert tutor_record.status == "ACTIVE"
