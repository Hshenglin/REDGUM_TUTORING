from fastapi import Request
from fastapi.templating import Jinja2Templates

from app.formatting import fmt_date, fmt_time

templates = Jinja2Templates(directory="app/templates")
templates.env.filters["time12"] = fmt_time
templates.env.filters["date_long"] = fmt_date


def flash(request: Request, message: str, category: str = "ok") -> None:
    flashes = list(request.session.get("flashes", []))
    flashes.append({"message": message, "category": category})
    request.session["flashes"] = flashes


def pop_flashes(request: Request) -> list[dict]:
    return request.session.pop("flashes", [])


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    ctx = {
        "request": request,
        "current_user": getattr(request.state, "user", None),
        "flashes": list(request.session.get("flashes", [])),
    }
    ctx.update(context or {})
    response = templates.TemplateResponse(request, name, ctx, status_code=status_code)
    request.session.pop("flashes", None)
    return response
