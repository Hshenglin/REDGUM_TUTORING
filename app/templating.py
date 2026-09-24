from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def flash(request: Request, message: str, category: str = "ok") -> None:
    request.session.setdefault("flashes", []).append({"message": message, "category": category})


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
