from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.models import AppUser, AvailabilityWindow, Tutor
from app.routers._helpers import get_or_404
from app.security import require_admin
from app.services import availability as availability_service
from app.templating import flash, render

router = APIRouter(tags=["availability"])


def _page(request: Request, tutor: Tutor, form: dict, errors: list[str],
          status_code: int = 200):
    return render(request, "tutors/availability.html", {
        "tutor": tutor,
        "windows": availability_service.list_windows(tutor),
        "form": form,
        "errors": errors,
    }, status_code=status_code)


@router.get("/tutors/{tutor_id}/availability")
def availability_view(tutor_id: int, request: Request, user: AppUser = Depends(require_admin),
                      db: OrmSession = Depends(get_db)):
    tutor = get_or_404(db, Tutor, tutor_id, "Tutor")
    return _page(request, tutor, {}, [])


@router.post("/tutors/{tutor_id}/availability")
def add_window(tutor_id: int, request: Request, day_of_week: str = Form(""),
               start_time: str = Form(""), end_time: str = Form(""),
               user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    tutor = get_or_404(db, Tutor, tutor_id, "Tutor")
    data, errors = availability_service.validate_window_form(day_of_week, start_time, end_time)
    if errors:
        return _page(request, tutor,
                     {"day_of_week": day_of_week, "start_time": start_time, "end_time": end_time},
                     errors, status_code=400)
    availability_service.add_window(db, tutor, **data)
    flash(request, f"Availability added for {tutor.name}.")
    return RedirectResponse(f"/tutors/{tutor.id}/availability", status_code=303)


@router.post("/availability/{window_id}/delete")
def delete_window(window_id: int, request: Request, user: AppUser = Depends(require_admin),
                  db: OrmSession = Depends(get_db)):
    window = get_or_404(db, AvailabilityWindow, window_id, "Availability window")
    tutor = window.tutor
    availability_service.delete_window(db, window)
    flash(request, "Availability removed.")
    return RedirectResponse(f"/tutors/{tutor.id}/availability", status_code=303)
