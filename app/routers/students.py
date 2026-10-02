from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.models import AppUser, Student
from app.routers._helpers import get_or_404
from app.security import require_admin
from app.services import schedule as schedule_service
from app.services import students as student_service
from app.templating import flash, render

router = APIRouter(prefix="/students", tags=["students"])


def _form(name: str, year_level: str, school: str, contact_name: str, contact_phone: str,
          contact_email: str, subjects: str) -> dict:
    return {"name": name, "year_level": year_level, "school": school, "contact_name": contact_name,
            "contact_phone": contact_phone, "contact_email": contact_email, "subjects": subjects}


@router.get("")
def list_view(request: Request, q: str = "", status: str = "",
              user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    return render(request, "students/list.html", {
        "students": student_service.list_students(db, q=q, status=status),
        "q": q,
        "status": status,
    })


@router.get("/new")
def new_form(request: Request, user: AppUser = Depends(require_admin)):
    return render(request, "students/form.html", {"student": None, "form": {}, "errors": []})


@router.post("/new")
def create(request: Request, name: str = Form(""), year_level: str = Form(""), school: str = Form(""),
           contact_name: str = Form(""), contact_phone: str = Form(""), contact_email: str = Form(""),
           subjects: str = Form(""), user: AppUser = Depends(require_admin),
           db: OrmSession = Depends(get_db)):
    data, errors = student_service.validate_student_form(
        name, year_level, school, contact_name, contact_phone, contact_email, subjects)
    form = _form(name, year_level, school, contact_name, contact_phone, contact_email, subjects)
    if errors:
        return render(request, "students/form.html",
                      {"student": None, "form": form, "errors": errors}, status_code=400)
    student = student_service.create_student(
        db, name=data["name"], year_level=data["year_level"], school=data["school"],
        contact_name=data["contact_name"], contact_phone=data["contact_phone"],
        contact_email=data["contact_email"], subjects=data["subjects"])
    flash(request, f"Student {student.name} added.")
    return RedirectResponse("/students", status_code=303)


@router.get("/{student_id}/edit")
def edit_form(student_id: int, request: Request, user: AppUser = Depends(require_admin),
              db: OrmSession = Depends(get_db)):
    student = get_or_404(db, Student, student_id, "Student")
    form = _form(student.name, str(student.year_level), student.school or "", student.contact_name,
                 student.contact_phone, student.contact_email or "", student.subjects or "")
    return render(request, "students/form.html", {"student": student, "form": form, "errors": []})


@router.post("/{student_id}/edit")
def edit(student_id: int, request: Request, name: str = Form(""), year_level: str = Form(""),
         school: str = Form(""), contact_name: str = Form(""), contact_phone: str = Form(""),
         contact_email: str = Form(""), subjects: str = Form(""),
         user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    student = get_or_404(db, Student, student_id, "Student")
    data, errors = student_service.validate_student_form(
        name, year_level, school, contact_name, contact_phone, contact_email, subjects)
    form = _form(name, year_level, school, contact_name, contact_phone, contact_email, subjects)
    if errors:
        return render(request, "students/form.html",
                      {"student": student, "form": form, "errors": errors}, status_code=400)
    student_service.update_student(
        db, student, name=data["name"], year_level=data["year_level"], school=data["school"],
        contact_name=data["contact_name"], contact_phone=data["contact_phone"],
        contact_email=data["contact_email"], subjects=data["subjects"])
    flash(request, f"Student {student.name} updated.")
    return RedirectResponse("/students", status_code=303)


@router.post("/{student_id}/status")
def set_status(student_id: int, request: Request, status: str = Form(""),
               user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    student = get_or_404(db, Student, student_id, "Student")
    if status not in ("ACTIVE", "INACTIVE"):
        raise HTTPException(status_code=400, detail="Invalid status")
    student_service.set_status(db, student, status)
    flash(request, f"Student {student.name} is now {status.lower()}.")
    return RedirectResponse("/students", status_code=303)


@router.get("/{student_id}/sessions")
def sessions_view(student_id: int, request: Request, user: AppUser = Depends(require_admin),
                  db: OrmSession = Depends(get_db)):
    student = get_or_404(db, Student, student_id, "Student")
    past, future = schedule_service.student_sessions(db, student_id, date.today())
    return render(request, "students/sessions.html",
                  {"student": student, "past": past, "future": future})
