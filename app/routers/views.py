from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.models import AppUser, Tutor
from app.security import require_admin, require_user
from app.services import schedule as schedule_service
from app.services import tutors as tutor_service
from app.templating import render
from app.validation import parse_date

router = APIRouter(tags=["views"])


@router.get("/")
def home(user: AppUser = Depends(require_user)):
    if user.role == "ADMIN":
        return RedirectResponse("/students", status_code=303)
    return RedirectResponse("/my-sessions", status_code=303)


@router.get("/schedule")
def schedule(request: Request, start: str = Query("", alias="date"), view: str = "week",
             tutor_id: str = "", user: AppUser = Depends(require_admin),
             db: OrmSession = Depends(get_db)):
    anchor = parse_date(start) or date.today()
    tutor_filter = int(tutor_id) if tutor_id.isdigit() else None

    if view == "day":
        sessions = schedule_service.sessions_between(db, anchor, anchor, tutor_filter)
        days = [(anchor, sessions)]
    else:
        range_start = schedule_service.week_start(anchor)
        sessions = schedule_service.sessions_between(
            db, range_start, schedule_service.week_days(range_start)[-1], tutor_filter)
        days = [(day, schedule_service.sessions_on(sessions, day))
                for day in schedule_service.week_days(range_start)]

    return render(request, "schedule.html", {
        "days": days,
        "view": "day" if view == "day" else "week",
        "anchor_iso": anchor.isoformat(),
        "tutor_id": tutor_id if tutor_filter else "",
        "tutors": tutor_service.list_tutors(db),
    })


@router.get("/my-sessions")
def my_sessions(request: Request, user: AppUser = Depends(require_user),
                db: OrmSession = Depends(get_db)):
    if user.tutor_id is None:
        return render(request, "my_sessions.html", {"tutor": None, "sessions": []})
    tutor = db.get(Tutor, user.tutor_id)
    sessions = schedule_service.upcoming_for_tutor(db, tutor.id, date.today())
    return render(request, "my_sessions.html", {"tutor": tutor, "sessions": sessions})
