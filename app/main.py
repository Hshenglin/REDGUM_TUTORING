from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import COOKIE_SECURE, SECRET_KEY, SESSION_MAX_AGE_SECONDS
from app.db import init_db
from app.routers import auth, availability, students, tutors, views
from app.security import RedirectToLogin
from app.templating import render


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.seed import seed_if_empty

    init_db()
    seed_if_empty()
    yield


app = FastAPI(title="Redgum Tutoring", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=SESSION_MAX_AGE_SECONDS,
    same_site="lax",
    https_only=COOKIE_SECURE,
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(tutors.router)
app.include_router(availability.router)
app.include_router(views.router)


@app.exception_handler(RedirectToLogin)
async def redirect_to_login(request: Request, exc: RedirectToLogin):
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    if exc.status_code in (400, 403, 404):
        headings = {400: "Invalid request", 403: "Not allowed", 404: "Page not found"}
        return render(request, "error.html",
                      {"message": exc.detail, "heading": headings[exc.status_code]},
                      status_code=exc.status_code)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
