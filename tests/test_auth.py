from app.models import AppUser
from app.security import hash_password

DEMO_PASSWORD = "redgum123"


def test_login_page_renders(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "Sign in" in r.text


def test_login_with_correct_credentials_redirects_home(client, admin):
    r = client.post("/login", data={"username": "deb", "password": DEMO_PASSWORD}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_login_with_wrong_password_shows_error(client, admin):
    r = client.post("/login", data={"username": "deb", "password": "wrong"})
    assert r.status_code == 400
    assert "Incorrect username or password" in r.text


def test_inactive_user_cannot_log_in(client, db_session):
    db_session.add(AppUser(username="gone", password_hash=hash_password(DEMO_PASSWORD),
                           role="ADMIN", status="INACTIVE"))
    db_session.commit()
    r = client.post("/login", data={"username": "gone", "password": DEMO_PASSWORD})
    assert r.status_code == 400
    assert "Incorrect username or password" in r.text


def test_anonymous_user_is_redirected_to_login(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_admin_lands_on_students_and_tutor_on_my_sessions(admin_client, tutor_client):
    assert admin_client.get("/", follow_redirects=False).headers["location"] == "/students"
    assert tutor_client.get("/", follow_redirects=False).headers["location"] == "/my-sessions"


def test_logout_clears_session(admin_client):
    r = admin_client.post("/logout", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"
    r = admin_client.get("/", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_signed_in_user_is_redirected_away_from_login(admin_client):
    r = admin_client.get("/login", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_signed_in_user_posting_login_is_redirected(admin_client):
    r = admin_client.post("/login", data={"username": "deb", "password": "wrong"},
                          follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_unknown_username_gets_the_same_generic_message(client, admin):
    r = client.post("/login", data={"username": "nobody", "password": "whatever"})
    assert r.status_code == 400
    assert "Incorrect username or password" in r.text


def test_login_establishes_a_session(client, admin):
    r = client.post("/login", data={"username": "deb", "password": DEMO_PASSWORD},
                    follow_redirects=False)
    assert r.status_code == 303
    follow_up = client.get("/", follow_redirects=False)
    assert follow_up.headers["location"] == "/students"


def test_session_cookie_is_httponly_and_lax(client, admin):
    r = client.post("/login", data={"username": "deb", "password": DEMO_PASSWORD},
                    follow_redirects=False)
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
