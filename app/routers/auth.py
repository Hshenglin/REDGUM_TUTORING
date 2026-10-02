from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.models import AppUser
from app.security import DUMMY_PASSWORD_HASH, verify_password
from app.templating import flash, render

router = APIRouter(tags=["auth"])


@router.get("/login")
def login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return render(request, "login.html", {"error": None, "username": ""})


@router.post("/login")
def login(request: Request, username: str = Form(""), password: str = Form(""),
          db: OrmSession = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    user = db.scalars(select(AppUser).where(AppUser.username == username.strip())).first()
    password_ok = verify_password(password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if user is None or user.status != "ACTIVE" or not password_ok:
        return render(request, "login.html",
                      {"error": "Incorrect username or password.", "username": username.strip()},
                      status_code=400)
    request.session.clear()
    request.session["user_id"] = user.id
    flash(request, f"Signed in as {user.username}.")
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "Signed out.")
    return RedirectResponse("/login", status_code=303)
