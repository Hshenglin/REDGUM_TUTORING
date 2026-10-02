from datetime import time

from sqlalchemy.orm import Session as OrmSession

from app.models import DAY_ORDER, OPEN_DAYS, AvailabilityWindow, Tutor
from app.validation import parse_time


def list_windows(tutor: Tutor) -> list[AvailabilityWindow]:
    return sorted(tutor.windows, key=lambda w: (DAY_ORDER.get(w.day_of_week, len(DAY_ORDER)), w.start_time))


def validate_window_form(day_of_week: str, start_time: str, end_time: str) -> tuple[dict, list[str]]:
    data: dict = {}
    errors: list[str] = []

    day = day_of_week.strip().upper()
    if day not in OPEN_DAYS:
        errors.append("Day must be one of Tuesday to Saturday.")
    else:
        data["day_of_week"] = day

    start = parse_time(start_time)
    if start is None:
        errors.append("Start time must look like 15:30.")
    else:
        data["start_time"] = start

    end = parse_time(end_time)
    if end is None:
        errors.append("End time must look like 18:00.")
    else:
        data["end_time"] = end

    if start is not None and end is not None and end <= start:
        errors.append("End time must be after the start time.")

    return data, errors


def add_window(db: OrmSession, tutor: Tutor, *, day_of_week: str, start_time: time,
               end_time: time) -> AvailabilityWindow:
    window = AvailabilityWindow(day_of_week=day_of_week, start_time=start_time, end_time=end_time)
    tutor.windows.append(window)
    db.commit()
    return window


def update_window(db: OrmSession, window: AvailabilityWindow, *, day_of_week: str, start_time: time,
                  end_time: time) -> AvailabilityWindow:
    window.day_of_week = day_of_week
    window.start_time = start_time
    window.end_time = end_time
    db.commit()
    return window


def delete_window(db: OrmSession, window: AvailabilityWindow) -> None:
    db.delete(window)
    db.commit()
