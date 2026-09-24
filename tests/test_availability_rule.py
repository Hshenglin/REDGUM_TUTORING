from datetime import date, time

import pytest

from app.errors import DomainError
from app.models import AvailabilityWindow, Tutor
from app.services.sessions import validate_slot

TUESDAY = date(2026, 8, 11)
WEDNESDAY = date(2026, 8, 12)
MONDAY = date(2026, 8, 10)


def make_tutor(*windows, status="ACTIVE"):
    tutor = Tutor(name="Tomás Ferreira", subjects="Physics", status=status)
    for day, start, end in windows:
        tutor.windows.append(AvailabilityWindow(day_of_week=day, start_time=start, end_time=end))
    return tutor


def tuesday_tutor():
    return make_tutor(("TUESDAY", time(15, 30), time(19, 0)))


def test_session_may_start_exactly_at_window_open():
    validate_slot(tuesday_tutor(), TUESDAY, time(15, 30), 60)


def test_session_may_end_exactly_at_window_close():
    validate_slot(tuesday_tutor(), TUESDAY, time(18, 0), 60)


def test_session_starting_before_window_is_refused():
    with pytest.raises(DomainError) as exc:
        validate_slot(tuesday_tutor(), TUESDAY, time(15, 0), 60)
    assert "would not fit" in exc.value.message


def test_session_running_past_window_close_is_refused_with_the_windows_listed():
    with pytest.raises(DomainError) as exc:
        validate_slot(tuesday_tutor(), TUESDAY, time(18, 30), 60)
    assert "3:30 pm" in exc.value.message
    assert "7:00 pm" in exc.value.message
    assert "would not fit" in exc.value.message


def test_day_with_no_window_is_refused():
    with pytest.raises(DomainError) as exc:
        validate_slot(tuesday_tutor(), MONDAY, time(15, 30), 60)
    assert "no availability on Monday" in exc.value.message


def test_ninety_minute_session_must_fit():
    tutor = make_tutor(("WEDNESDAY", time(15, 30), time(18, 0)))
    with pytest.raises(DomainError):
        validate_slot(tutor, WEDNESDAY, time(17, 0), 90)
    validate_slot(tutor, WEDNESDAY, time(16, 30), 90)


def test_only_sixty_or_ninety_minutes():
    with pytest.raises(DomainError) as exc:
        validate_slot(tuesday_tutor(), TUESDAY, time(16, 0), 45)
    assert "60 or 90" in exc.value.message


def test_inactive_tutor_is_refused():
    tutor = make_tutor(("TUESDAY", time(15, 30), time(19, 0)), status="INACTIVE")
    with pytest.raises(DomainError) as exc:
        validate_slot(tutor, TUESDAY, time(16, 0), 60)
    assert "not an active tutor" in exc.value.message


def test_session_may_use_a_second_window_on_the_same_day():
    tutor = make_tutor(
        ("TUESDAY", time(15, 30), time(17, 0)),
        ("TUESDAY", time(18, 0), time(19, 30)),
    )
    validate_slot(tutor, TUESDAY, time(18, 0), 60)


def test_date_maps_to_the_right_weekday():
    tutor = make_tutor(("TUESDAY", time(15, 30), time(19, 0)))
    with pytest.raises(DomainError) as exc:
        validate_slot(tutor, WEDNESDAY, time(16, 0), 60)
    assert "no availability on Wednesday" in exc.value.message


def test_session_crossing_midnight_is_refused():
    tutor = make_tutor(("THURSDAY", time(22, 0), time(23, 59)))
    with pytest.raises(DomainError) as exc:
        validate_slot(tutor, date(2026, 8, 13), time(23, 30), 60)
    assert "past midnight" in exc.value.message


def test_session_ending_at_the_last_minute_of_the_day_is_allowed():
    tutor = make_tutor(("THURSDAY", time(22, 0), time(23, 59)))
    validate_slot(tutor, date(2026, 8, 13), time(22, 59), 60)
