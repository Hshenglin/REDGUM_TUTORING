import bcrypt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.models import AppUser


class RedirectToLogin(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-constant-time-login")


def current_user(request: Request, db: OrmSession = Depends(get_db)) -> AppUser | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    user = db.get(AppUser, user_id)
    if user is None or user.status != "ACTIVE":
        request.session.pop("user_id", None)
        return None
    request.state.user = user
    return user


def require_user(user: AppUser | None = Depends(current_user)) -> AppUser:
    if user is None:
        raise RedirectToLogin()
    return user


def require_admin(user: AppUser = Depends(require_user)) -> AppUser:
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    return user
