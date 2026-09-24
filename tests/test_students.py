from app.models import Student


def test_admin_sees_student_list(admin_client, make_student):
    make_student(name="Ella Nguyen")
    r = admin_client.get("/students")
    assert r.status_code == 200
    assert "Ella Nguyen" in r.text


def test_create_student(admin_client, db_session):
    r = admin_client.post("/students/new", data={
        "name": "Kai Lombardo", "year_level": "11", "school": "Willowbank State High",
        "contact_name": "Gina Lombardo", "contact_phone": "0418 330 297",
        "contact_email": "", "subjects": "Physics",
    }, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/students"
    student = db_session.query(Student).filter_by(name="Kai Lombardo").one()
    assert student.year_level == 11
    assert student.status == "ACTIVE"


def test_missing_required_fields_are_reported_and_nothing_is_saved(admin_client, db_session):
    r = admin_client.post("/students/new", data={
        "name": "", "year_level": "", "contact_name": "", "contact_phone": "",
    })
    assert r.status_code == 400
    assert "Student name is required." in r.text
    assert "Year level is required." in r.text
    assert "Family contact name is required." in r.text
    assert "Family contact phone is required." in r.text
    assert db_session.query(Student).count() == 0


def test_invalid_year_level_is_reported(admin_client, db_session):
    r = admin_client.post("/students/new", data={
        "name": "X", "year_level": "13", "contact_name": "Y", "contact_phone": "0400",
    })
    assert r.status_code == 400
    assert "Year level must be between 5 and 12." in r.text
    assert db_session.query(Student).count() == 0


def test_edit_student(admin_client, make_student, db_session):
    student = make_student(name="Ella Nguyen")
    r = admin_client.post(f"/students/{student.id}/edit", data={
        "name": "Ella Nguyen", "year_level": "12", "school": "Limestone High",
        "contact_name": "Mai Nguyen", "contact_phone": "0412 660 118",
        "contact_email": "", "subjects": "Physics",
    }, follow_redirects=False)
    assert r.status_code == 303
    db_session.refresh(student)
    assert student.year_level == 12


def test_deactivate_and_reactivate(admin_client, make_student, db_session):
    student = make_student()
    admin_client.post(f"/students/{student.id}/status", data={"status": "INACTIVE"})
    db_session.refresh(student)
    assert student.status == "INACTIVE"
    admin_client.post(f"/students/{student.id}/status", data={"status": "ACTIVE"})
    db_session.refresh(student)
    assert student.status == "ACTIVE"


def test_search_filters_by_name(admin_client, make_student):
    make_student(name="Ella Nguyen")
    make_student(name="Kai Lombardo")
    r = admin_client.get("/students?q=Kai")
    assert "Kai Lombardo" in r.text
    assert "Ella Nguyen" not in r.text


def test_tutor_cannot_access_students(tutor_client):
    assert tutor_client.get("/students").status_code == 403


def test_unknown_student_edit_returns_404(admin_client):
    assert admin_client.get("/students/9999/edit").status_code == 404


def test_edit_validation_failure_keeps_the_record(admin_client, make_student, db_session):
    student = make_student(name="Ella Nguyen")
    r = admin_client.post(f"/students/{student.id}/edit", data={
        "name": "", "year_level": "12", "contact_name": "Mai Nguyen", "contact_phone": "0412 660 118",
    })
    assert r.status_code == 400
    assert "Student name is required." in r.text
    db_session.refresh(student)
    assert student.name == "Ella Nguyen"
    assert student.year_level == 11


def test_invalid_status_is_rejected(admin_client, make_student, db_session):
    student = make_student()
    r = admin_client.post(f"/students/{student.id}/status", data={"status": "DELETED"})
    assert r.status_code == 400
    assert "Invalid status" in r.text
    db_session.refresh(student)
    assert student.status == "ACTIVE"


def test_status_and_edit_on_unknown_student_return_404(admin_client):
    assert admin_client.post("/students/9999/edit", data={
        "name": "X", "year_level": "11", "contact_name": "Y", "contact_phone": "0400",
    }).status_code == 404
    assert admin_client.post("/students/9999/status", data={"status": "INACTIVE"}).status_code == 404


def test_inactive_students_are_listed_by_default(admin_client, make_student):
    make_student(name="Ruth Callaghan", status="INACTIVE")
    r = admin_client.get("/students")
    assert "Ruth Callaghan" in r.text


def test_non_numeric_year_level_is_reported(admin_client, db_session):
    r = admin_client.post("/students/new", data={
        "name": "X", "year_level": "eleven", "contact_name": "Y", "contact_phone": "0400",
    })
    assert r.status_code == 400
    assert "Year level must be a whole number between 5 and 12." in r.text
