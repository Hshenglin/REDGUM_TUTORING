from datetime import date, time


def fmt_time(value: time) -> str:
    return value.strftime("%I:%M %p").lstrip("0").lower()


def fmt_date(value: date) -> str:
    return f"{value.strftime('%a')} {value.day} {value.strftime('%b %Y')}"
