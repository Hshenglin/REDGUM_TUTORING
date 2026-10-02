from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.errors import DomainError
from app.models import AppUser, SESSION_LENGTHS, Session
from app.routers._helpers import get_or_404
from app.security import require_admin
from app.services import sessions as session_service
from app.services import students as student_service
from app.services import tutors as tutor_service
from app.templating import flash, render
from app.validation import parse_date, parse_time

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


def _get_session(db: OrmSession, session_id: int) -> Session:
    return get_or_404(db, Session, session_id, "Session")


@router.get("/{session_id}/edit")
def edit_form(session_id: int, request: Request, user: AppUser = Depends(require_admin),
              db: OrmSession = Depends(get_db)):
    session = _get_session(db, session_id)
    form = {
        "session_date": session.session_date.isoformat(),
        "start_time": session.start_time.strftime("%H:%M"),
        "length_minutes": str(session.length_minutes),
    }
    return render(request, "sessions/edit.html", {"session": session, "form": form, "errors": []})


@router.post("/{session_id}/edit")
def edit(session_id: int, request: Request, session_date: str = Form(""),
         start_time: str = Form(""), length_minutes: str = Form(""),
         user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    session = _get_session(db, session_id)
    form = {"session_date": session_date, "start_time": start_time, "length_minutes": length_minutes}
    errors: list[str] = []

    parsed_date = parse_date(session_date)
    if parsed_date is None:
        errors.append("Date must look like 2026-08-11.")
    parsed_start = parse_time(start_time)
    if parsed_start is None:
        errors.append("Start time must look like 15:30.")
    length = int(length_minutes) if length_minutes.isdigit() else None
    if length not in SESSION_LENGTHS:
        errors.append("Length must be 60 or 90 minutes.")

    if not errors:
        try:
            session_service.move_session(db, session, session_date=parsed_date,
                                         start_time=parsed_start, length_minutes=length)
        except DomainError as exc:
            errors.append(exc.message)

    if errors:
        return render(request, "sessions/edit.html", {"session": session, "form": form, "errors": errors},
                      status_code=400)
    flash(request, "Session moved.")
    return RedirectResponse("/sessions", status_code=303)


@router.post("/{session_id}/cancel")
def cancel(session_id: int, request: Request, user: AppUser = Depends(require_admin),
           db: OrmSession = Depends(get_db)):
    session = _get_session(db, session_id)
    try:
        session_service.cancel_session(db, session)
    except DomainError as exc:
        flash(request, exc.message, "error")
        return RedirectResponse("/sessions", status_code=303)
    flash(request, "Session cancelled.")
    return RedirectResponse("/sessions", status_code=303)


@router.post("/{session_id}/status")
def set_status(session_id: int, request: Request, outcome: str = Form(""),
               user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    session = _get_session(db, session_id)
    try:
        session_service.set_outcome(db, session, outcome)
    except DomainError as exc:
        flash(request, exc.message, "error")
        return RedirectResponse("/sessions", status_code=303)
    flash(request, f"Session marked {outcome.lower()}.")
    return RedirectResponse("/sessions", status_code=303)
