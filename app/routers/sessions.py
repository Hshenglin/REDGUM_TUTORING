from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.errors import DomainError
from app.models import AppUser
from app.security import require_admin
from app.services import sessions as session_service
from app.services import students as student_service
from app.services import tutors as tutor_service
from app.templating import flash, render
from app.validation import parse_date

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _form_context(db: OrmSession, form: dict, errors: list[str]) -> dict:
    return {
        "form": form,
        "errors": errors,
        "students": student_service.list_students(db, status="ACTIVE"),
        "tutors": tutor_service.bookable_tutors(db),
    }


@router.get("")
def list_view(request: Request, date_from: str = "", date_to: str = "", tutor_id: str = "",
              student_id: str = "", status: str = "",
              user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    filters = {"date_from": date_from, "date_to": date_to, "tutor_id": tutor_id,
               "student_id": student_id, "status": status}
    return render(request, "sessions/list.html", {
        "sessions": session_service.list_sessions(
            db,
            date_from=parse_date(date_from),
            date_to=parse_date(date_to),
            tutor_id=int(tutor_id) if tutor_id.isdigit() else None,
            student_id=int(student_id) if student_id.isdigit() else None,
            status=status,
        ),
        "tutors": tutor_service.list_tutors(db),
        "students": student_service.list_students(db),
        "filters": filters,
    })


@router.get("/new")
def new_form(request: Request, user: AppUser = Depends(require_admin),
             db: OrmSession = Depends(get_db)):
    return render(request, "sessions/form.html", _form_context(db, {"length_minutes": "60"}, []))


@router.post("/new")
def create(request: Request, student_id: str = Form(""), tutor_id: str = Form(""),
           subject: str = Form(""), session_date: str = Form(""), start_time: str = Form(""),
           length_minutes: str = Form(""), user: AppUser = Depends(require_admin),
           db: OrmSession = Depends(get_db)):
    form = {"student_id": student_id, "tutor_id": tutor_id, "subject": subject,
            "session_date": session_date, "start_time": start_time, "length_minutes": length_minutes}
    data, errors = session_service.validate_session_form(
        db, student_id, tutor_id, subject, session_date, start_time, length_minutes)
    if not errors:
        try:
            session_service.book_session(db, **data)
        except DomainError as exc:
            errors.append(exc.message)
    if errors:
        return render(request, "sessions/form.html", _form_context(db, form, errors),
                      status_code=400)
    flash(request, "Session booked.")
    return RedirectResponse("/sessions", status_code=303)
