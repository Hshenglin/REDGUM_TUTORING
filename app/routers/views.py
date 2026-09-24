from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.models import AppUser
from app.security import require_user

router = APIRouter(tags=["views"])


@router.get("/")
def home(user: AppUser = Depends(require_user)):
    if user.role == "ADMIN":
        return RedirectResponse("/students", status_code=303)
    return RedirectResponse("/my-sessions", status_code=303)
