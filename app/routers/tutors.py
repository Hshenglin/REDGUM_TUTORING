from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.models import AppUser, Tutor
from app.routers._helpers import get_or_404
from app.security import require_admin
from app.services import tutors as tutor_service
from app.templating import flash, render

router = APIRouter(prefix="/tutors", tags=["tutors"])


def _form(name: str, phone: str, subjects: str) -> dict:
    return {"name": name, "phone": phone, "subjects": subjects}


@router.get("")
def list_view(request: Request, q: str = "", status: str = "",
              user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    return render(request, "tutors/list.html", {
        "tutors": tutor_service.list_tutors(db, q=q, status=status),
        "q": q,
        "status": status,
    })


@router.get("/new")
def new_form(request: Request, user: AppUser = Depends(require_admin)):
    return render(request, "tutors/form.html", {"tutor": None, "form": {}, "errors": []})


@router.post("/new")
def create(request: Request, name: str = Form(""), phone: str = Form(""), subjects: str = Form(""),
           user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    data, errors = tutor_service.validate_tutor_form(name, phone, subjects)
    form = _form(name, phone, subjects)
    if errors:
        return render(request, "tutors/form.html",
                      {"tutor": None, "form": form, "errors": errors}, status_code=400)
    tutor = tutor_service.create_tutor(
        db, name=data["name"], phone=data["phone"], subjects=data["subjects"])
    flash(request, f"Tutor {tutor.name} added.")
    return RedirectResponse("/tutors", status_code=303)


@router.get("/{tutor_id}/edit")
def edit_form(tutor_id: int, request: Request, user: AppUser = Depends(require_admin),
              db: OrmSession = Depends(get_db)):
    tutor = get_or_404(db, Tutor, tutor_id, "Tutor")
    form = _form(tutor.name, tutor.phone or "", tutor.subjects)
    return render(request, "tutors/form.html", {"tutor": tutor, "form": form, "errors": []})


@router.post("/{tutor_id}/edit")
def edit(tutor_id: int, request: Request, name: str = Form(""), phone: str = Form(""),
         subjects: str = Form(""), user: AppUser = Depends(require_admin),
         db: OrmSession = Depends(get_db)):
    tutor = get_or_404(db, Tutor, tutor_id, "Tutor")
    data, errors = tutor_service.validate_tutor_form(name, phone, subjects)
    form = _form(name, phone, subjects)
    if errors:
        return render(request, "tutors/form.html",
                      {"tutor": tutor, "form": form, "errors": errors}, status_code=400)
    tutor_service.update_tutor(
        db, tutor, name=data["name"], phone=data["phone"], subjects=data["subjects"])
    flash(request, f"Tutor {tutor.name} updated.")
    return RedirectResponse("/tutors", status_code=303)


@router.post("/{tutor_id}/status")
def set_status(tutor_id: int, request: Request, status: str = Form(""),
               user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    tutor = get_or_404(db, Tutor, tutor_id, "Tutor")
    if status not in ("ACTIVE", "INACTIVE"):
        raise HTTPException(status_code=400, detail="Invalid status")
    tutor_service.set_status(db, tutor, status)
    flash(request, f"Tutor {tutor.name} is now {status.lower()}.")
    return RedirectResponse("/tutors", status_code=303)
