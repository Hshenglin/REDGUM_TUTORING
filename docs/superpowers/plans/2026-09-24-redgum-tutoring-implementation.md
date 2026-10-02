# Redgum Tutoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一个可运行的辅导中心排课系统(FastAPI + Jinja2 服务端渲染),支持学生/导师/可用时段管理、排课与改期时的**可用时段校验**、日/周课表与导师视图,并满足课程 DoD(干净 checkout 可跑、每故事一分支、pytest 全覆盖)。

**Architecture:** 单体 FastAPI 应用,SQLAlchemy 2.x 访问 SQLite,Jinja2 服务端渲染表单(PRG + 会话 flash),Starlette SessionMiddleware 签名 cookie 做登录态;核心领域逻辑集中在一个纯函数 `validate_slot()`,可脱离数据库单元测试。

**Tech Stack:** Python 3.10+(开发用 3.12)、FastAPI、Uvicorn、Jinja2、SQLAlchemy 2.x、bcrypt、python-multipart、itsdangerous;pytest + httpx TestClient。

**Spec:** `docs/superpowers/specs/2026-09-24-redgum-tutoring-design.md`

---

## 0. 执行约定

**环境(本机已验证):** 系统 Python 3.9 太旧;使用 `uv` 安装的 Python 3.12 建虚拟环境。

```bash
# 每个 Task 开始前(首次)
uv venv --python 3.12
uv pip install -r requirements.txt
# 之后统一用:
uv run pytest
uv run uvicorn app.main:app --port 8000
```

**分支策略:** 每个故事一个分支,基于上一个故事分支;`main` 只保留设计文档提交。

```bash
# Task 1 起:
git checkout -b story/01-foundation main
# Task 2 起:
git checkout -b story/02-auth story/01-foundation
# ...以此类推
```

**提交规范:** `feat(story-NN): ...` / `test(story-NN): ...` / `fix(story-NN): ...` / `docs(story-NN): ...`,每个故事 1–3 个 commit。提交用:

```bash
git -c user.name="boyforest" -c user.email="boyforest@users.noreply.github.com" commit -m "..."
```

**约定:**
- 所有时间按本地时间直接比较,无时区处理;`date`/`time` 用 Python 标准库类型。
- 表单校验失败:**HTTP 400 + 重新渲染表单并显示错误**,不写入任何数据;成功:**303 重定向(PRG)+ flash 消息**。
- 未登录访问受保护路由 → 303 重定向 `/login`;非 ADMIN 访问管理路由 → **403 错误页**。
- 每个 Task 的测试文件独立;`pytest` 为 DoD 验收命令。
- 计划中所有相对路径均相对仓库根 `~/redgum-tutoring`。

---

## 文件地图

| 文件 | 职责 |
|------|------|
| `requirements.txt` | 依赖清单 |
| `app/config.py` | 环境变量与默认值(密钥、会话时长、数据库 URL) |
| `app/db.py` | engine、`SessionLocal`、`Base`、`get_db`、`init_db` |
| `app/models.py` | Student、Tutor、AvailabilityWindow、Session、AppUser |
| `app/security.py` | 密码哈希、`current_user`/`require_user`/`require_admin` 依赖、`RedirectToLogin` |
| `app/templating.py` | Jinja2 实例、`render()`、flash 读写 |
| `app/validation.py` | 表单解析辅助(int/date/time + 错误收集) |
| `app/errors.py` | `DomainError`(领域校验失败) |
| `app/seed.py` | 幂等种子数据(空库才写) |
| `app/main.py` | 应用装配:中间件、静态目录、异常处理、路由注册、lifespan(建表+种子) |
| `app/services/students.py` | 学生 CRUD + 搜索 + 表单校验 |
| `app/services/tutors.py` | 导师 CRUD + 可排课导师列表 + 表单校验 |
| `app/services/availability.py` | 可用时段增改删 + 表单校验 |
| `app/services/sessions.py` | **`validate_slot()` 核心规则** + 排课/改期/取消/状态 |
| `app/services/schedule.py` | 日/周课表、学生历史、导师即将到来 |
| `app/routers/auth.py` | `/login`、`/logout` |
| `app/routers/students.py` | `/students*` |
| `app/routers/tutors.py` | `/tutors*`、`/availability/*` |
| `app/routers/sessions.py` | `/sessions*` |
| `app/routers/views.py` | `/`、`/schedule`、`/my-sessions` |
| `app/templates/**` | base、login、error、students/*、tutors/*、sessions/*、schedule、my_sessions |
| `app/static/style.css` | 唯一样式表(本地,不依赖 CDN) |
| `tests/conftest.py` | 内存 SQLite、依赖覆盖、客户端与数据工厂 |
| `tests/test_*.py` | 见各 Task |
| `README.md` / `docs/handover.md` / `docs/jira-import.csv` | Task 10 交付物 |

---

## Task 1: 项目骨架与数据模型(`story/01-foundation`)

**Files:**
- Create: `requirements.txt`, `.gitignore`(已存在,确认覆盖 `.venv/`)、`app/__init__.py`、`app/services/__init__.py`、`app/routers/__init__.py`
- Create: `app/config.py`, `app/db.py`, `app/models.py`, `app/templating.py`, `app/errors.py`, `app/seed.py`, `app/main.py`
- Create: `app/templates/base.html`, `app/templates/error.html`, `app/static/style.css`
- Create: `tests/__init__.py`, `tests/conftest.py`, `tests/test_foundation.py`

- [ ] **Step 1: 建分支与虚拟环境**

```bash
git checkout -b story/01-foundation main
uv venv --python 3.12
```

- [ ] **Step 2: 写 `requirements.txt`**

```
fastapi>=0.115,<1.0
uvicorn[standard]>=0.32,<1.0
jinja2>=3.1,<4.0
SQLAlchemy>=2.0,<3.0
bcrypt>=4.2,<5.0
python-multipart>=0.0.18
itsdangerous>=2.2,<3.0
pytest>=8.3,<9.0
httpx>=0.28,<1.0
```

```bash
uv pip install -r requirements.txt
```

Expected: 安装成功,无编译错误。

- [ ] **Step 3: 写 `app/config.py`、`app/db.py`**

```python
# app/config.py
import os

SECRET_KEY = os.environ.get("REDGUM_SECRET_KEY", "dev-secret-change-me")
SESSION_MAX_AGE_SECONDS = 60 * 60 * 12
DATABASE_URL = os.environ.get("REDGUM_DATABASE_URL", "sqlite:///./redgum.db")
COOKIE_SECURE = os.environ.get("REDGUM_COOKIE_SECURE", "").lower() in ("1", "true", "yes")
```

```python
# app/db.py
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app import models  # noqa: F401  确保模型已注册
    Base.metadata.create_all(bind=engine)
```

- [ ] **Step 4: 写 `app/models.py`**

```python
# app/models.py
from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

DAY_NAMES = ("MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY")
OPEN_DAYS = ("TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY")
SESSION_LENGTHS = (60, 90)
SESSION_STATUSES = ("BOOKED", "ATTENDED", "CANCELLED", "MISSED")


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Student(Base):
    __tablename__ = "student"
    __table_args__ = (CheckConstraint("year_level BETWEEN 5 AND 12", name="ck_student_year"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    year_level: Mapped[int]
    school: Mapped[str | None] = mapped_column(String(120))
    contact_name: Mapped[str] = mapped_column(String(100))
    contact_phone: Mapped[str] = mapped_column(String(20))
    contact_email: Mapped[str | None] = mapped_column(String(120))
    subjects: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Tutor(Base):
    __tablename__ = "tutor"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(20))
    subjects: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    windows: Mapped[list[AvailabilityWindow]] = relationship(
        back_populates="tutor", cascade="all, delete-orphan"
    )


class AvailabilityWindow(Base):
    __tablename__ = "availability_window"
    __table_args__ = (UniqueConstraint("tutor_id", "day_of_week", "start_time", "end_time", name="uq_window"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutor.id"))
    day_of_week: Mapped[str] = mapped_column(String(10))
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    tutor: Mapped[Tutor] = relationship(back_populates="windows")


class Session(Base):
    __tablename__ = "session"
    __table_args__ = (Index("ix_session_tutor_date", "tutor_id", "session_date"), Index("ix_session_student", "student_id"), CheckConstraint("length_minutes IN (60, 90)", name="ck_session_length"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student.id"))
    tutor_id: Mapped[int] = mapped_column(ForeignKey("tutor.id"))
    subject: Mapped[str] = mapped_column(String(100))
    session_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    length_minutes: Mapped[int]
    status: Mapped[str] = mapped_column(String(20), default="BOOKED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    student: Mapped[Student] = relationship()
    tutor: Mapped[Tutor] = relationship()


class AppUser(Base):
    __tablename__ = "app_user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))
    tutor_id: Mapped[int | None] = mapped_column(ForeignKey("tutor.id"))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    tutor: Mapped[Tutor | None] = relationship()
```

- [ ] **Step 5: 写 `app/errors.py`、`app/templating.py`**

```python
# app/errors.py
class DomainError(Exception):
    """Raised when a domain rule refuses an operation. The message is shown to the user."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
```

```python
# app/templating.py
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
```

- [ ] **Step 6: 写 `app/templates/base.html`、`app/templates/error.html`**

```html
<!-- app/templates/base.html -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}Redgum Tutoring{% endblock %}</title>
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="/">Redgum Tutoring</a>
    {% if current_user %}
      <nav>
        {% if current_user.role == 'ADMIN' %}
          <a href="/schedule">Schedule</a>
          <a href="/sessions">Sessions</a>
          <a href="/students">Students</a>
          <a href="/tutors">Tutors</a>
        {% else %}
          <a href="/my-sessions">My sessions</a>
        {% endif %}
      </nav>
      <div class="whoami">
        <span>{{ current_user.username }} · {{ 'Administrator' if current_user.role == 'ADMIN' else 'Tutor' }}</span>
        <form method="post" action="/logout"><button type="submit" class="link">Sign out</button></form>
      </div>
    {% endif %}
  </header>
  <main>
    {% for f in flashes %}
      <div class="flash flash-{{ f.category }}">{{ f.message }}</div>
    {% endfor %}
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

```html
<!-- app/templates/error.html -->
{% extends "base.html" %}
{% block title %}{{ heading or 'Error' }} — Redgum Tutoring{% endblock %}
{% block content %}
  <section class="card">
    <h1>{{ heading or 'Something went wrong' }}</h1>
    <p>{{ message }}</p>
    <p><a href="/">Back to the home page</a></p>
  </section>
{% endblock %}
```

- [ ] **Step 7: 写 `app/static/style.css`**

```css
:root {
  --ink: #1f2933;
  --muted: #6b7280;
  --line: #d9dee3;
  --bg: #f7f8fa;
  --accent: #8c2f39;
  --accent-dark: #6f2129;
  --ok-bg: #e7f4ea;
  --ok-ink: #20572f;
  --warn-bg: #fdecec;
  --warn-ink: #8a2020;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--ink);
  background: var(--bg);
}

.topbar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 24px;
  background: #fff;
  border-bottom: 1px solid var(--line);
}

.brand { font-weight: 700; color: var(--accent); text-decoration: none; }
.topbar nav { display: flex; gap: 16px; flex: 1; }
.topbar nav a { color: var(--ink); text-decoration: none; }
.topbar nav a:hover { color: var(--accent); }
.whoami { display: flex; align-items: center; gap: 12px; color: var(--muted); font-size: 14px; }

main { max-width: 1040px; margin: 24px auto; padding: 0 24px; }

.card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

h1 { font-size: 22px; margin: 0 0 12px; }
h2 { font-size: 17px; margin: 24px 0 8px; }

.flash { padding: 10px 14px; border-radius: 6px; margin-bottom: 12px; }
.flash-ok { background: var(--ok-bg); color: var(--ok-ink); }
.flash-error { background: var(--warn-bg); color: var(--warn-ink); }

table { width: 100%; border-collapse: collapse; background: #fff; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; }
th { font-size: 13px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); }

.toolbar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.filters { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

form.inline { display: inline; }

button, .button {
  font: inherit;
  padding: 6px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  text-decoration: none;
  color: var(--ink);
}

button.primary, .button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
button.primary:hover, .button.primary:hover { background: var(--accent-dark); }
button.link { border: none; background: none; color: var(--accent); padding: 0; }
button.danger { color: var(--warn-ink); }

.field { margin-bottom: 14px; }
.field label { display: block; font-size: 13px; color: var(--muted); margin-bottom: 4px; }
.field input, .field select { font: inherit; padding: 7px 9px; border: 1px solid var(--line); border-radius: 6px; width: 100%; max-width: 360px; }
.field .hint { font-size: 12px; color: var(--muted); margin-top: 4px; }

.errors { background: var(--warn-bg); color: var(--warn-ink); border-radius: 6px; padding: 10px 14px; margin-bottom: 14px; }
.errors ul { margin: 4px 0 0 18px; }

.status { font-size: 12px; padding: 2px 8px; border-radius: 999px; background: #eef1f4; color: var(--muted); }
.status-ACTIVE, .status-ATTENDED { background: var(--ok-bg); color: var(--ok-ink); }
.status-INACTIVE, .status-CANCELLED, .status-MISSED { background: var(--warn-bg); color: var(--warn-ink); }
.status-BOOKED { background: #e8eefc; color: #24407a; }

.muted { color: var(--muted); }
.empty { color: var(--muted); padding: 12px 0; }
.actions { display: flex; gap: 6px; flex-wrap: wrap; }
```

- [ ] **Step 8: 写 `app/main.py`**

```python
# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.middleware.sessions import SessionMiddleware

from app.config import COOKIE_SECURE, SECRET_KEY, SESSION_MAX_AGE_SECONDS
from app.db import init_db
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


@app.exception_handler(RedirectToLogin)
async def redirect_to_login(request: Request, exc: RedirectToLogin):
    return RedirectResponse("/login", status_code=303)


@app.exception_handler(HTTPException)
async def http_exception(request: Request, exc: HTTPException):
    if exc.status_code in (403, 404):
        heading = "Not allowed" if exc.status_code == 403 else "Page not found"
        return render(request, "error.html", {"message": exc.detail, "heading": heading},
                      status_code=exc.status_code)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers)
```

注意:`app/security.py`(Step 9)必须先存在,否则 `main.py` 导入失败。

- [ ] **Step 9: 写 `app/security.py`(本任务只用到 `hash_password` 与 `RedirectToLogin`,其余为 Task 2 准备)**

```python
# app/security.py
import bcrypt
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.models import AppUser


class RedirectToLogin(Exception):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


DUMMY_PASSWORD_HASH = hash_password("dummy-password-for-constant-time-login")


def current_user(request: Request, db: OrmSession = Depends(get_db)) -> AppUser | None:
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    user = db.get(AppUser, user_id)
    if user is None or user.status != "ACTIVE":
        request.session.pop("user_id", None)
        return None
    request.state.user = user
    return user


def require_user(user: AppUser | None = Depends(current_user)) -> AppUser:
    if user is None:
        raise RedirectToLogin()
    return user


def require_admin(user: AppUser = Depends(require_user)) -> AppUser:
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Administrator access is required.")
    return user
```

- [ ] **Step 10: 写 `app/seed.py`(完整案例数据;空库才写入)**

```python
# app/seed.py
from datetime import date, time, timedelta

from app.db import SessionLocal
from app.models import AppUser, AvailabilityWindow, Session, Student, Tutor
from app.security import hash_password

DEMO_PASSWORD = "redgum123"

TUTORS = [
    {
        "name": "Tomás Ferreira",
        "phone": "0407 512 884",
        "subjects": "Physics 10-12, Chemistry 10-12, Maths Methods 11-12",
        "status": "ACTIVE",
        "windows": [
            ("TUESDAY", time(15, 30), time(19, 0)),
            ("WEDNESDAY", time(15, 30), time(18, 0)),
            ("THURSDAY", time(16, 0), time(18, 30)),
            ("SATURDAY", time(9, 0), time(12, 30)),
        ],
    },
    {
        "name": "Helen Vasquez",
        "phone": "0407 220 118",
        "subjects": "Maths 5-12",
        "status": "ACTIVE",
        "windows": [
            ("WEDNESDAY", time(15, 0), time(18, 30)),
            ("SATURDAY", time(9, 0), time(13, 0)),
        ],
    },
    {
        "name": "Priyanka Shah",
        "phone": "0407 883 402",
        "subjects": "Maths 5-10, Science 7-10",
        "status": "ACTIVE",
        "windows": [
            ("TUESDAY", time(16, 0), time(19, 0)),
            ("THURSDAY", time(15, 30), time(18, 0)),
        ],
    },
    {
        "name": "Marcus Webb",
        "phone": "0407 145 990",
        "subjects": "English 7-10",
        "status": "INACTIVE",
        "windows": [("FRIDAY", time(15, 30), time(18, 0))],
    },
]

STUDENTS = [
    {"name": "Ella Nguyen", "year_level": 11, "school": "Limestone High", "contact_name": "Mai Nguyen",
     "contact_phone": "0412 660 118", "contact_email": "mai.nguyen@example.com", "subjects": "Physics"},
    {"name": "Jayden Pike", "year_level": 10, "school": "Limestone High", "contact_name": "Rebecca Pike",
     "contact_phone": "0413 220 774", "contact_email": None, "subjects": "Maths"},
    {"name": "Sara Habib", "year_level": 12, "school": "Ipswich Girls Grammar", "contact_name": "Nadia Habib",
     "contact_phone": "0414 981 205", "contact_email": "nadia.habib@example.com", "subjects": "Chemistry"},
    {"name": "Oliver Brandt", "year_level": 9, "school": "Ipswich State High", "contact_name": "Petra Brandt",
     "contact_phone": "0415 330 619", "contact_email": None, "subjects": "Maths"},
    {"name": "Mia Okafor", "year_level": 12, "school": "Ipswich Girls Grammar", "contact_name": "Chidi Okafor",
     "contact_phone": "0416 774 082", "contact_email": "chidi.okafor@example.com", "subjects": "Maths Methods"},
    {"name": "Kai Lombardo", "year_level": 11, "school": "Willowbank State High", "contact_name": "Gina Lombardo",
     "contact_phone": "0418 330 297", "contact_email": "g.lombardo@example.com", "subjects": "Physics, Maths Methods"},
    {"name": "Noah Fischer", "year_level": 8, "school": "Ipswich State High", "contact_name": "Anna Fischer",
     "contact_phone": "0417 552 361", "contact_email": None, "subjects": "Maths"},
]

# 文档 B(第 5 周,2026-08-11 至 08-15)的原样课时;状态:A=ATTENDED, N=MISSED, C/CANCELLED=CANCELLED
DIARY_WEEK = [
    ("TUE", date(2026, 8, 11), time(15, 30), "Ferreira", "Ella Nguyen", "Physics", 60, "ATTENDED"),
    ("TUE", date(2026, 8, 11), time(16, 45), "Ferreira", "Jayden Pike", "Maths", 60, "MISSED"),
    ("TUE", date(2026, 8, 11), time(18, 0), "Ferreira", "Sara Habib", "Chemistry", 60, "ATTENDED"),
    ("WED", date(2026, 8, 12), time(15, 30), "Vasquez", "Oliver Brandt", "Maths", 60, "ATTENDED"),
    ("WED", date(2026, 8, 12), time(16, 45), "Vasquez", "Mia Okafor", "Maths Methods", 90, "ATTENDED"),
    ("THU", date(2026, 8, 13), time(16, 0), "Ferreira", "Ella Nguyen", "Physics", 60, "ATTENDED"),
    ("THU", date(2026, 8, 13), time(17, 15), "Ferreira", "Kai Lombardo", "Physics", 60, "CANCELLED"),
    ("SAT", date(2026, 8, 15), time(9, 0), "Ferreira", "Jayden Pike", "Maths", 60, "ATTENDED"),
    ("SAT", date(2026, 8, 15), time(10, 15), "Vasquez", "Sara Habib", "Chemistry", 90, "ATTENDED"),
    ("SAT", date(2026, 8, 15), time(12, 0), "Vasquez", "Oliver Brandt", "Maths", 60, "CANCELLED"),
]


def seed_if_empty() -> None:
    db = SessionLocal()
    try:
        if db.query(Student).count() > 0 or db.query(AppUser).count() > 0:
            return

        tutors = {}
        for spec in TUTORS:
            tutor = Tutor(name=spec["name"], phone=spec["phone"], subjects=spec["subjects"], status=spec["status"])
            for day, start, end in spec["windows"]:
                tutor.windows.append(AvailabilityWindow(day_of_week=day, start_time=start, end_time=end))
            db.add(tutor)
            tutors[spec["name"].split()[0]] = tutor
            tutors[spec["name"].split()[-1]] = tutor
        db.flush()

        students = {}
        for spec in STUDENTS:
            student = Student(**spec, status="ACTIVE")
            db.add(student)
            students[spec["name"]] = student
        db.flush()

        db.add_all([
            AppUser(username="deb", password_hash=hash_password(DEMO_PASSWORD), role="ADMIN", status="ACTIVE"),
            AppUser(username="helen", password_hash=hash_password(DEMO_PASSWORD), role="ADMIN",
                    tutor_id=tutors["Helen"].id, status="ACTIVE"),
            AppUser(username="tomas", password_hash=hash_password(DEMO_PASSWORD), role="TUTOR",
                    tutor_id=tutors["Tomás"].id, status="ACTIVE"),
        ])

        for _day, session_date, start, tutor_key, student_name, subject, length, status in DIARY_WEEK:
            db.add(Session(
                student_id=students[student_name].id,
                tutor_id=tutors[tutor_key].id,
                subject=subject,
                session_date=session_date,
                start_time=start,
                length_minutes=length,
                status=status,
            ))

        # 下周的 BOOKED 课时(相对今天动态生成),保证任何时间演示都有"即将到来"数据
        today = date.today()
        next_tuesday = today + timedelta(days=(1 - today.weekday()) % 7 or 7)
        upcoming = [
            (next_tuesday, time(15, 30), "Ferreira", "Ella Nguyen", "Physics", 60),
            (next_tuesday, time(16, 45), "Ferreira", "Kai Lombardo", "Physics", 60),
            (next_tuesday, time(18, 0), "Ferreira", "Sara Habib", "Chemistry", 60),
            (next_tuesday + timedelta(days=1), time(15, 30), "Vasquez", "Oliver Brandt", "Maths", 60),
            (next_tuesday + timedelta(days=2), time(16, 0), "Ferreira", "Ella Nguyen", "Physics", 60),
            (next_tuesday + timedelta(days=4), time(9, 0), "Ferreira", "Jayden Pike", "Maths", 60),
        ]
        for session_date, start, tutor_key, student_name, subject, length in upcoming:
            db.add(Session(
                student_id=students[student_name].id,
                tutor_id=tutors[tutor_key].id,
                subject=subject,
                session_date=session_date,
                start_time=start,
                length_minutes=length,
                status="BOOKED",
            ))

        db.commit()
    finally:
        db.close()
```

注意:导师字典同时以名字和姓氏为键——`AppUser` 用名字(`Helen`/`Tomás`),课表数据用姓氏(`Ferreira`/`Vasquez`)。

- [ ] **Step 11: 写 `tests/conftest.py` 与 `tests/test_foundation.py`**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app
from app.models import AppUser, AvailabilityWindow, Session, Student, Tutor
from app.security import hash_password

DEMO_PASSWORD = "redgum123"


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture(autouse=True)
def _clear_overrides_after_test():
    yield
    app.dependency_overrides.clear()


def _make_client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture()
def client(db_session):
    c = _make_client(db_session)
    yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin(db_session):
    user = AppUser(username="deb", password_hash=hash_password(DEMO_PASSWORD), role="ADMIN", status="ACTIVE")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def tutor_record(db_session):
    tutor = Tutor(name="Tomás Ferreira", phone="0407 512 884",
                  subjects="Physics 10-12, Chemistry 10-12", status="ACTIVE")
    tutor.windows.extend([
        AvailabilityWindow(day_of_week="TUESDAY", start_time=time(15, 30), end_time=time(19, 0)),
        AvailabilityWindow(day_of_week="THURSDAY", start_time=time(16, 0), end_time=time(18, 30)),
        AvailabilityWindow(day_of_week="SATURDAY", start_time=time(9, 0), end_time=time(12, 30)),
    ])
    db_session.add(tutor)
    db_session.commit()
    return tutor


@pytest.fixture()
def tutor_user(db_session, tutor_record):
    user = AppUser(username="tomas", password_hash=hash_password(DEMO_PASSWORD), role="TUTOR",
                   tutor_id=tutor_record.id, status="ACTIVE")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def admin_client(db_session, admin):
    c = _make_client(db_session)
    response = c.post("/login", data={"username": "deb", "password": DEMO_PASSWORD}, follow_redirects=False)
    assert response.status_code == 303
    yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def tutor_client(db_session, tutor_user):
    c = _make_client(db_session)
    response = c.post("/login", data={"username": "tomas", "password": DEMO_PASSWORD}, follow_redirects=False)
    assert response.status_code == 303
    yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def make_student(db_session):
    def _make(name="Ella Nguyen", year_level=11, status="ACTIVE", **kwargs):
        student = Student(
            name=name, year_level=year_level, school=kwargs.get("school", "Limestone High"),
            contact_name=kwargs.get("contact_name", "Mai Nguyen"),
            contact_phone=kwargs.get("contact_phone", "0412 660 118"),
            contact_email=kwargs.get("contact_email"), subjects=kwargs.get("subjects", "Physics"),
            status=status,
        )
        db_session.add(student)
        db_session.commit()
        return student
    return _make


@pytest.fixture()
def make_session(db_session):
    def _make(student, tutor, session_date=date(2026, 8, 11), start_time=time(15, 30),
              length_minutes=60, subject="Physics", status="BOOKED"):
        session = Session(
            student_id=student.id, tutor_id=tutor.id, subject=subject,
            session_date=session_date, start_time=start_time,
            length_minutes=length_minutes, status=status,
        )
        db_session.add(session)
        db_session.commit()
        return session
    return _make
```

注意:上面的 `conftest.py` 用到 `time`、`date`,文件头需补:

```python
from datetime import date, time
```

另外需创建空的 `tests/__init__.py`,使 pytest 将仓库根加入 `sys.path`(否则 `uv run pytest` 无法导入 `app`)。

```python
# tests/test_foundation.py
from sqlalchemy import inspect

from app.models import Student


def test_tables_are_created(db_session):
    tables = set(inspect(db_session.get_bind()).get_table_names())
    assert {"student", "tutor", "availability_window", "session", "app_user"} <= tables


def test_student_round_trip(db_session):
    student = Student(name="Ella Nguyen", year_level=11, contact_name="Mai Nguyen", contact_phone="0412 660 118")
    db_session.add(student)
    db_session.commit()
    db_session.expire_all()

    loaded = db_session.get(Student, student.id)
    assert loaded.name == "Ella Nguyen"
    assert loaded.year_level == 11
    assert loaded.status == "ACTIVE"
    assert loaded.created_at is not None


def test_unknown_path_returns_404(client):
    assert client.get("/no-such-page").status_code == 404
```

- [ ] **Step 12: 运行测试(应通过)**

```bash
uv run pytest -q
```

Expected: `3 passed`。

- [ ] **Step 13: 手工验证应用启动与种子数据**

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/static/style.css
uv run python -c "from app.db import SessionLocal; from app.models import Student, Tutor, Session, AppUser; db=SessionLocal(); print(Student.__name__, db.query(Student).count()); print('tutors', db.query(Tutor).count()); print('sessions', db.query(Session).count()); print('users', db.query(AppUser).count()); db.close()"
kill %1
```

Expected: 静态文件 `200`;打印 `students 7`、`tutors 4`、`sessions 16`、`users 3`。

- [ ] **Step 14: 提交**

```bash
git add -A
git commit -m "feat(story-01): FastAPI skeleton, SQLAlchemy models, seed data and foundation tests"
```

---

## Task 2: 登录与角色(`story/02-auth`)

**Files:**
- Create: `app/routers/auth.py`, `app/routers/views.py`, `app/templates/login.html`
- Modify: `app/main.py`(注册路由)
- Create: `tests/test_auth.py`

- [ ] **Step 1: 建分支**

```bash
git checkout -b story/02-auth story/01-foundation
```

- [ ] **Step 2: 写失败测试 `tests/test_auth.py`**

```python
from app.models import AppUser
from app.security import hash_password

DEMO_PASSWORD = "redgum123"


def test_login_page_renders(client):
    r = client.get("/login")
    assert r.status_code == 200
    assert "Sign in" in r.text


def test_login_with_correct_credentials_redirects_home(client, admin):
    r = client.post("/login", data={"username": "deb", "password": DEMO_PASSWORD}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_login_with_wrong_password_shows_error(client, admin):
    r = client.post("/login", data={"username": "deb", "password": "wrong"})
    assert r.status_code == 400
    assert "Incorrect username or password" in r.text


def test_inactive_user_cannot_log_in(client, db_session):
    db_session.add(AppUser(username="gone", password_hash=hash_password(DEMO_PASSWORD),
                           role="ADMIN", status="INACTIVE"))
    db_session.commit()
    r = client.post("/login", data={"username": "gone", "password": DEMO_PASSWORD})
    assert r.status_code == 400
    assert "Incorrect username or password" in r.text


def test_anonymous_user_is_redirected_to_login(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_admin_lands_on_students_and_tutor_on_my_sessions(admin_client, tutor_client):
    assert admin_client.get("/", follow_redirects=False).headers["location"] == "/students"
    assert tutor_client.get("/", follow_redirects=False).headers["location"] == "/my-sessions"


def test_logout_clears_session(admin_client):
    r = admin_client.post("/logout", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"
    r = admin_client.get("/", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_signed_in_user_is_redirected_away_from_login(admin_client):
    r = admin_client.get("/login", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_signed_in_user_posting_login_is_redirected(admin_client):
    r = admin_client.post("/login", data={"username": "deb", "password": "wrong"},
                          follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/"


def test_unknown_username_gets_the_same_generic_message(client, admin):
    r = client.post("/login", data={"username": "nobody", "password": "whatever"})
    assert r.status_code == 400
    assert "Incorrect username or password" in r.text


def test_login_establishes_a_session(client, admin):
    r = client.post("/login", data={"username": "deb", "password": DEMO_PASSWORD},
                    follow_redirects=False)
    assert r.status_code == 303
    follow_up = client.get("/", follow_redirects=False)
    assert follow_up.headers["location"] == "/students"


def test_session_cookie_is_httponly_and_lax(client, admin):
    r = client.post("/login", data={"username": "deb", "password": DEMO_PASSWORD},
                    follow_redirects=False)
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
```

- [ ] **Step 3: 运行确认失败**

```bash
uv run pytest tests/test_auth.py -q
```

Expected: 全部失败(`/login` 返回 404)。

- [ ] **Step 4: 写 `app/routers/auth.py` 与 `app/routers/views.py`**

```python
# app/routers/auth.py
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.models import AppUser
from app.security import DUMMY_PASSWORD_HASH, verify_password
from app.templating import flash, render

router = APIRouter(tags=["auth"])


@router.get("/login")
def login_form(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    return render(request, "login.html", {"error": None, "username": ""})


@router.post("/login")
def login(request: Request, username: str = Form(""), password: str = Form(""),
          db: OrmSession = Depends(get_db)):
    if request.session.get("user_id"):
        return RedirectResponse("/", status_code=303)
    user = db.scalars(select(AppUser).where(AppUser.username == username.strip())).first()
    password_ok = verify_password(password, user.password_hash if user else DUMMY_PASSWORD_HASH)
    if user is None or user.status != "ACTIVE" or not password_ok:
        return render(request, "login.html",
                      {"error": "Incorrect username or password.", "username": username.strip()},
                      status_code=400)
    request.session.clear()
    request.session["user_id"] = user.id
    flash(request, f"Signed in as {user.username}.")
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "Signed out.")
    return RedirectResponse("/login", status_code=303)
```

```python
# app/routers/views.py
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.models import AppUser
from app.security import require_user

router = APIRouter(tags=["views"])


@router.get("/")
def home(user: AppUser = Depends(require_user)):
    if user.role == "ADMIN":
        return RedirectResponse("/students", status_code=303)
    return RedirectResponse("/my-sessions", status_code=303)
```

- [ ] **Step 5: 写 `app/templates/login.html`**

```html
{% extends "base.html" %}
{% block title %}Sign in — Redgum Tutoring{% endblock %}
{% block content %}
  <section class="card" style="max-width: 420px; margin: 40px auto;">
    <h1>Sign in</h1>
    {% if error %}<div class="errors" role="alert">{{ error }}</div>{% endif %}
    <form method="post" action="/login">
      <div class="field">
        <label for="username">Username</label>
        <input id="username" name="username" value="{{ username }}" autocomplete="username" autofocus required>
      </div>
      <div class="field">
        <label for="password">Password</label>
        <input id="password" name="password" type="password" autocomplete="current-password" required>
      </div>
      <button type="submit" class="primary">Sign in</button>
    </form>
  </section>
{% endblock %}
```

- [ ] **Step 6: 修改 `app/main.py` 注册路由**

在 `from app.templating import render` 之后加:

```python
from app.routers import auth, views
```

在 `app.mount("/static", ...)` 之后加:

```python
app.include_router(auth.router)
app.include_router(views.router)
```

- [ ] **Step 7: 运行测试(应通过)**

```bash
uv run pytest tests/test_auth.py -q
```

Expected: `12 passed`。

- [ ] **Step 8: 手工验证**

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/login
curl -s -i -X POST http://localhost:8000/login -d "username=deb&password=redgum123" | grep -iE "^HTTP|^location"
kill %1
```

Expected: `/login` 返回 `200`;登录返回 `303` 且 `location: /`。浏览器可打开 `http://localhost:8000/login` 查看页面样式。

- [ ] **Step 9: 提交**

```bash
git add -A
git commit -m "feat(story-02): session login, role guards and login page"
```

---

## Task 3: 管理员维护学生(`story/03-students`)

**Files:**
- Create: `app/routers/_helpers.py`, `app/services/students.py`, `app/routers/students.py`, `app/templates/students/list.html`, `app/templates/students/form.html`
- Modify: `app/main.py`(注册路由)
- Create: `tests/test_students.py`

- [ ] **Step 1: 建分支**

```bash
git checkout -b story/03-students story/02-auth
```

- [ ] **Step 2: 写失败测试 `tests/test_students.py`**

```python
from app.models import Student


def test_admin_sees_student_list(admin_client, make_student):
    make_student(name="Ella Nguyen")
    r = admin_client.get("/students")
    assert r.status_code == 200
    assert "Ella Nguyen" in r.text


def test_create_student(admin_client, db_session):
    r = admin_client.post("/students/new", data={
        "name": "Kai Lombardo", "year_level": "11", "school": "Willowbank State High",
        "contact_name": "Gina Lombardo", "contact_phone": "0418 330 297",
        "contact_email": "", "subjects": "Physics",
    }, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/students"
    student = db_session.query(Student).filter_by(name="Kai Lombardo").one()
    assert student.year_level == 11
    assert student.status == "ACTIVE"


def test_missing_required_fields_are_reported_and_nothing_is_saved(admin_client, db_session):
    r = admin_client.post("/students/new", data={
        "name": "", "year_level": "", "contact_name": "", "contact_phone": "",
    })
    assert r.status_code == 400
    assert "Student name is required." in r.text
    assert "Year level is required." in r.text
    assert "Family contact name is required." in r.text
    assert "Family contact phone is required." in r.text
    assert db_session.query(Student).count() == 0


def test_invalid_year_level_is_reported(admin_client, db_session):
    r = admin_client.post("/students/new", data={
        "name": "X", "year_level": "13", "contact_name": "Y", "contact_phone": "0400",
    })
    assert r.status_code == 400
    assert "Year level must be between 5 and 12." in r.text
    assert db_session.query(Student).count() == 0


def test_edit_student(admin_client, make_student, db_session):
    student = make_student(name="Ella Nguyen")
    r = admin_client.post(f"/students/{student.id}/edit", data={
        "name": "Ella Nguyen", "year_level": "12", "school": "Limestone High",
        "contact_name": "Mai Nguyen", "contact_phone": "0412 660 118",
        "contact_email": "", "subjects": "Physics",
    }, follow_redirects=False)
    assert r.status_code == 303
    db_session.refresh(student)
    assert student.year_level == 12


def test_deactivate_and_reactivate(admin_client, make_student, db_session):
    student = make_student()
    admin_client.post(f"/students/{student.id}/status", data={"status": "INACTIVE"})
    db_session.refresh(student)
    assert student.status == "INACTIVE"
    admin_client.post(f"/students/{student.id}/status", data={"status": "ACTIVE"})
    db_session.refresh(student)
    assert student.status == "ACTIVE"


def test_search_filters_by_name(admin_client, make_student):
    make_student(name="Ella Nguyen")
    make_student(name="Kai Lombardo")
    r = admin_client.get("/students?q=Kai")
    assert "Kai Lombardo" in r.text
    assert "Ella Nguyen" not in r.text


def test_tutor_cannot_access_students(tutor_client):
    assert tutor_client.get("/students").status_code == 403


def test_unknown_student_edit_returns_404(admin_client):
    assert admin_client.get("/students/9999/edit").status_code == 404
```

- [ ] **Step 3: 运行确认失败**

```bash
uv run pytest tests/test_students.py -q
```

Expected: 全部失败(404)。

- [ ] **Step 4: 写 `app/routers/_helpers.py` 与 `app/services/students.py`**

```python
# app/routers/_helpers.py
from fastapi import HTTPException
from sqlalchemy.orm import Session as OrmSession


def get_or_404(db: OrmSession, model, object_id: int, label: str):
    obj = db.get(model, object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return obj
```

```python
# app/services/students.py
from sqlalchemy import or_, select
from sqlalchemy.orm import Session as OrmSession

from app.models import Student


def list_students(db: OrmSession, q: str = "", status: str = "") -> list[Student]:
    stmt = select(Student)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Student.name.ilike(like), Student.contact_name.ilike(like)))
    if status in ("ACTIVE", "INACTIVE"):
        stmt = stmt.where(Student.status == status)
    return list(db.scalars(stmt.order_by(Student.name)))


def validate_student_form(name: str, year_level: str, contact_name: str, contact_phone: str) -> tuple[dict, list[str]]:
    data: dict = {}
    errors: list[str] = []

    name = name.strip()
    if not name:
        errors.append("Student name is required.")
    data["name"] = name

    year_level = year_level.strip()
    if not year_level:
        errors.append("Year level is required.")
    else:
        try:
            year = int(year_level)
        except ValueError:
            errors.append("Year level must be a whole number between 5 and 12.")
        else:
            if not 5 <= year <= 12:
                errors.append("Year level must be between 5 and 12.")
            else:
                data["year_level"] = year

    contact_name = contact_name.strip()
    if not contact_name:
        errors.append("Family contact name is required.")
    data["contact_name"] = contact_name

    contact_phone = contact_phone.strip()
    if not contact_phone:
        errors.append("Family contact phone is required.")
    data["contact_phone"] = contact_phone

    return data, errors


def create_student(db: OrmSession, *, name: str, year_level: int, school: str, contact_name: str,
                   contact_phone: str, contact_email: str, subjects: str) -> Student:
    student = Student(name=name, year_level=year_level, school=school.strip() or None,
                      contact_name=contact_name, contact_phone=contact_phone,
                      contact_email=contact_email.strip() or None,
                      subjects=subjects.strip() or None, status="ACTIVE")
    db.add(student)
    db.commit()
    return student


def update_student(db: OrmSession, student: Student, *, name: str, year_level: int, school: str,
                   contact_name: str, contact_phone: str, contact_email: str, subjects: str) -> Student:
    student.name = name
    student.year_level = year_level
    student.school = school.strip() or None
    student.contact_name = contact_name
    student.contact_phone = contact_phone
    student.contact_email = contact_email.strip() or None
    student.subjects = subjects.strip() or None
    db.commit()
    return student


def set_status(db: OrmSession, student: Student, status: str) -> Student:
    student.status = status
    db.commit()
    return student
```

- [ ] **Step 5: 写 `app/routers/students.py`**

```python
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.models import AppUser, Student
from app.routers._helpers import get_or_404
from app.security import require_admin
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
    data, errors = student_service.validate_student_form(name, year_level, contact_name, contact_phone)
    form = _form(name, year_level, school, contact_name, contact_phone, contact_email, subjects)
    if errors:
        return render(request, "students/form.html",
                      {"student": None, "form": form, "errors": errors}, status_code=400)
    student = student_service.create_student(
        db, name=data["name"], year_level=data["year_level"], school=school,
        contact_name=data["contact_name"], contact_phone=data["contact_phone"],
        contact_email=contact_email, subjects=subjects)
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
    data, errors = student_service.validate_student_form(name, year_level, contact_name, contact_phone)
    form = _form(name, year_level, school, contact_name, contact_phone, contact_email, subjects)
    if errors:
        return render(request, "students/form.html",
                      {"student": student, "form": form, "errors": errors}, status_code=400)
    student_service.update_student(
        db, student, name=data["name"], year_level=data["year_level"], school=school,
        contact_name=data["contact_name"], contact_phone=data["contact_phone"],
        contact_email=contact_email, subjects=subjects)
    flash(request, f"Student {student.name} updated.")
    return RedirectResponse("/students", status_code=303)


@router.post("/{student_id}/status")
def set_status(student_id: int, request: Request, status: str = Form(...),
               user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    if status not in ("ACTIVE", "INACTIVE"):
        raise HTTPException(status_code=400, detail="Invalid status")
    student = get_or_404(db, Student, student_id, "Student")
    student_service.set_status(db, student, status)
    flash(request, f"Student {student.name} is now {status.lower()}.")
    return RedirectResponse("/students", status_code=303)
```

- [ ] **Step 6: 写 `app/templates/students/list.html` 与 `app/templates/students/form.html`**

```html
<!-- app/templates/students/list.html -->
{% extends "base.html" %}
{% block title %}Students — Redgum Tutoring{% endblock %}
{% block content %}
<div class="toolbar">
  <h1>Students</h1>
  <a class="button primary" href="/students/new">Add student</a>
</div>
<form method="get" action="/students" class="filters card">
  <div class="field" style="margin:0">
    <label for="q">Search</label>
    <input id="q" name="q" value="{{ q }}" placeholder="Student or family contact">
  </div>
  <div class="field" style="margin:0">
    <label for="status">Status</label>
    <select id="status" name="status">
      <option value="" {% if not status %}selected{% endif %}>All</option>
      <option value="ACTIVE" {% if status == 'ACTIVE' %}selected{% endif %}>Active</option>
      <option value="INACTIVE" {% if status == 'INACTIVE' %}selected{% endif %}>Inactive</option>
    </select>
  </div>
  <button type="submit">Filter</button>
</form>
{% if students %}
<table>
  <thead>
    <tr><th>Name</th><th>Year</th><th>School</th><th>Family contact</th><th>Subjects</th><th>Status</th><th></th></tr>
  </thead>
  <tbody>
  {% for s in students %}
    <tr>
      <td>{{ s.name }}</td>
      <td>{{ s.year_level }}</td>
      <td>{{ s.school or '—' }}</td>
      <td>{{ s.contact_name }}<br><span class="muted">{{ s.contact_phone }}</span></td>
      <td>{{ s.subjects or '—' }}</td>
      <td><span class="status status-{{ s.status }}">{{ s.status.title() }}</span></td>
      <td class="actions">
        <a class="button" href="/students/{{ s.id }}/edit">Edit</a>
        <form class="inline" method="post" action="/students/{{ s.id }}/status">
          <input type="hidden" name="status" value="{{ 'INACTIVE' if s.status == 'ACTIVE' else 'ACTIVE' }}">
          <button type="submit">{{ 'Deactivate' if s.status == 'ACTIVE' else 'Activate' }}</button>
        </form>
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% else %}
<p class="empty">No students match.</p>
{% endif %}
{% endblock %}
```

```html
<!-- app/templates/students/form.html -->
{% extends "base.html" %}
{% block title %}{{ 'Edit student' if student else 'Add student' }} — Redgum Tutoring{% endblock %}
{% block content %}
<section class="card" style="max-width: 560px;">
  <h1>{{ 'Edit student' if student else 'Add student' }}</h1>
  {% if errors %}
    <div class="errors">
      <strong>Please fix the following:</strong>
      <ul>{% for e in errors %}<li>{{ e }}</li>{% endfor %}</ul>
    </div>
  {% endif %}
  <form method="post" action="{{ ('/students/' ~ student.id ~ '/edit') if student else '/students/new' }}">
    <div class="field">
      <label for="name">Student name *</label>
      <input id="name" name="name" value="{{ form.get('name', '') }}">
    </div>
    <div class="field">
      <label for="year_level">Year level * (5–12)</label>
      <input id="year_level" name="year_level" value="{{ form.get('year_level', '') }}">
    </div>
    <div class="field">
      <label for="school">School</label>
      <input id="school" name="school" value="{{ form.get('school', '') }}">
    </div>
    <div class="field">
      <label for="contact_name">Family contact name *</label>
      <input id="contact_name" name="contact_name" value="{{ form.get('contact_name', '') }}">
    </div>
    <div class="field">
      <label for="contact_phone">Family contact phone *</label>
      <input id="contact_phone" name="contact_phone" value="{{ form.get('contact_phone', '') }}">
    </div>
    <div class="field">
      <label for="contact_email">Family contact email</label>
      <input id="contact_email" name="contact_email" value="{{ form.get('contact_email', '') }}">
    </div>
    <div class="field">
      <label for="subjects">Subjects wanted</label>
      <input id="subjects" name="subjects" value="{{ form.get('subjects', '') }}"
             placeholder="Physics, Maths Methods">
    </div>
    <button type="submit" class="primary">Save</button>
    <a class="button" href="/students">Cancel</a>
  </form>
</section>
{% endblock %}
```

- [ ] **Step 7: 修改 `app/main.py` 注册路由**

```python
from app.routers import auth, students, views
```

```python
app.include_router(students.router)
```

- [ ] **Step 8: 运行测试(应通过)**

```bash
uv run pytest tests/test_students.py -q
```

Expected: `9 passed`。

- [ ] **Step 9: 手工验证**

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s -c /tmp/rg.jar -X POST http://localhost:8000/login -d "username=deb&password=redgum123" -o /dev/null
curl -s -b /tmp/rg.jar http://localhost:8000/students | grep -c "Ella Nguyen"
kill %1
```

Expected: 输出 `1`(列表里能看到种子学生)。浏览器登录后可点 Students 查看。

- [ ] **Step 10: 提交**

```bash
git add -A
git commit -m "feat(story-03): student records with search, edit and deactivate"
```

---

## Task 4: 管理员维护导师(`story/04-tutors`)

**Files:**
- Create: `app/services/tutors.py`, `app/routers/tutors.py`, `app/templates/tutors/list.html`, `app/templates/tutors/form.html`
- Modify: `app/main.py`(注册路由)
- Create: `tests/test_tutors.py`

- [ ] **Step 1: 建分支**

```bash
git checkout -b story/04-tutors story/03-students
```

- [ ] **Step 2: 写失败测试 `tests/test_tutors.py`**

```python
from app.models import Tutor


def test_admin_sees_tutor_list(admin_client, tutor_record):
    r = admin_client.get("/tutors")
    assert r.status_code == 200
    assert "Tomás Ferreira" in r.text


def test_create_tutor(admin_client, db_session):
    r = admin_client.post("/tutors/new", data={
        "name": "Priyanka Shah", "phone": "0407 883 402",
        "subjects": "Maths 5-10, Science 7-10",
    }, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/tutors"
    tutor = db_session.query(Tutor).filter_by(name="Priyanka Shah").one()
    assert tutor.status == "ACTIVE"


def test_name_and_subjects_are_required(admin_client, db_session):
    r = admin_client.post("/tutors/new", data={"name": "", "phone": "", "subjects": ""})
    assert r.status_code == 400
    assert "Tutor name is required." in r.text
    assert "Subjects are required." in r.text
    assert db_session.query(Tutor).count() == 0


def test_edit_tutor(admin_client, tutor_record, db_session):
    r = admin_client.post(f"/tutors/{tutor_record.id}/edit", data={
        "name": "Tomás Ferreira", "phone": "0407 512 884",
        "subjects": "Physics 10-12, Chemistry 10-12, Maths Methods 11-12",
    }, follow_redirects=False)
    assert r.status_code == 303
    db_session.refresh(tutor_record)
    assert "Maths Methods" in tutor_record.subjects


def test_deactivate_tutor_keeps_sessions(admin_client, tutor_record, make_student, make_session, db_session):
    session = make_session(make_student(), tutor_record)
    admin_client.post(f"/tutors/{tutor_record.id}/status", data={"status": "INACTIVE"})
    db_session.refresh(tutor_record)
    assert tutor_record.status == "INACTIVE"
    assert session.status == "BOOKED"


def test_tutor_cannot_access_tutor_admin(tutor_client):
    assert tutor_client.get("/tutors").status_code == 403


def test_unknown_tutor_edit_returns_404(admin_client):
    assert admin_client.get("/tutors/9999/edit").status_code == 404
```

- [ ] **Step 3: 运行确认失败**

```bash
uv run pytest tests/test_tutors.py -q
```

Expected: 全部失败(404)。

- [ ] **Step 4: 写 `app/services/tutors.py`**

```python
from sqlalchemy import or_, select
from sqlalchemy.orm import Session as OrmSession

from app.models import Tutor


def list_tutors(db: OrmSession, q: str = "", status: str = "") -> list[Tutor]:
    stmt = select(Tutor)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Tutor.name.ilike(like), Tutor.subjects.ilike(like)))
    if status in ("ACTIVE", "INACTIVE"):
        stmt = stmt.where(Tutor.status == status)
    return list(db.scalars(stmt.order_by(Tutor.name)))


def bookable_tutors(db: OrmSession) -> list[Tutor]:
    return list(db.scalars(select(Tutor).where(Tutor.status == "ACTIVE").order_by(Tutor.name)))


def validate_tutor_form(name: str, subjects: str) -> tuple[dict, list[str]]:
    data: dict = {}
    errors: list[str] = []

    name = name.strip()
    if not name:
        errors.append("Tutor name is required.")
    data["name"] = name

    subjects = subjects.strip()
    if not subjects:
        errors.append("Subjects are required.")
    data["subjects"] = subjects

    return data, errors


def create_tutor(db: OrmSession, *, name: str, phone: str, subjects: str) -> Tutor:
    tutor = Tutor(name=name, phone=phone.strip() or None, subjects=subjects, status="ACTIVE")
    db.add(tutor)
    db.commit()
    return tutor


def update_tutor(db: OrmSession, tutor: Tutor, *, name: str, phone: str, subjects: str) -> Tutor:
    tutor.name = name
    tutor.phone = phone.strip() or None
    tutor.subjects = subjects
    db.commit()
    return tutor


def set_status(db: OrmSession, tutor: Tutor, status: str) -> Tutor:
    tutor.status = status
    db.commit()
    return tutor
```

- [ ] **Step 5: 写 `app/routers/tutors.py`**

```python
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
    data, errors = tutor_service.validate_tutor_form(name, subjects)
    form = {"name": name, "phone": phone, "subjects": subjects}
    if errors:
        return render(request, "tutors/form.html",
                      {"tutor": None, "form": form, "errors": errors}, status_code=400)
    tutor = tutor_service.create_tutor(db, name=data["name"], phone=phone, subjects=data["subjects"])
    flash(request, f"Tutor {tutor.name} added.")
    return RedirectResponse("/tutors", status_code=303)


@router.get("/{tutor_id}/edit")
def edit_form(tutor_id: int, request: Request, user: AppUser = Depends(require_admin),
              db: OrmSession = Depends(get_db)):
    tutor = get_or_404(db, Tutor, tutor_id, "Tutor")
    form = {"name": tutor.name, "phone": tutor.phone or "", "subjects": tutor.subjects}
    return render(request, "tutors/form.html", {"tutor": tutor, "form": form, "errors": []})


@router.post("/{tutor_id}/edit")
def edit(tutor_id: int, request: Request, name: str = Form(""), phone: str = Form(""),
         subjects: str = Form(""), user: AppUser = Depends(require_admin),
         db: OrmSession = Depends(get_db)):
    tutor = get_or_404(db, Tutor, tutor_id, "Tutor")
    data, errors = tutor_service.validate_tutor_form(name, subjects)
    form = {"name": name, "phone": phone, "subjects": subjects}
    if errors:
        return render(request, "tutors/form.html",
                      {"tutor": tutor, "form": form, "errors": errors}, status_code=400)
    tutor_service.update_tutor(db, tutor, name=data["name"], phone=phone, subjects=data["subjects"])
    flash(request, f"Tutor {tutor.name} updated.")
    return RedirectResponse("/tutors", status_code=303)


@router.post("/{tutor_id}/status")
def set_status(tutor_id: int, request: Request, status: str = Form(...),
               user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    if status not in ("ACTIVE", "INACTIVE"):
        raise HTTPException(status_code=400, detail="Invalid status")
    tutor = get_or_404(db, Tutor, tutor_id, "Tutor")
    tutor_service.set_status(db, tutor, status)
    flash(request, f"Tutor {tutor.name} is now {status.lower()}.")
    return RedirectResponse("/tutors", status_code=303)
```

- [ ] **Step 6: 写 `app/templates/tutors/list.html` 与 `app/templates/tutors/form.html`**

```html
<!-- app/templates/tutors/list.html -->
{% extends "base.html" %}
{% block title %}Tutors — Redgum Tutoring{% endblock %}
{% block content %}
<div class="toolbar">
  <h1>Tutors</h1>
  <a class="button primary" href="/tutors/new">Add tutor</a>
</div>
<form method="get" action="/tutors" class="filters card">
  <div class="field" style="margin:0">
    <label for="q">Search</label>
    <input id="q" name="q" value="{{ q }}" placeholder="Tutor or subject">
  </div>
  <div class="field" style="margin:0">
    <label for="status">Status</label>
    <select id="status" name="status">
      <option value="" {% if not status %}selected{% endif %}>All</option>
      <option value="ACTIVE" {% if status == 'ACTIVE' %}selected{% endif %}>Active</option>
      <option value="INACTIVE" {% if status == 'INACTIVE' %}selected{% endif %}>Inactive</option>
    </select>
  </div>
  <button type="submit">Filter</button>
</form>
{% if tutors %}
<table>
  <thead><tr><th>Name</th><th>Subjects</th><th>Phone</th><th>Availability</th><th>Status</th><th></th></tr></thead>
  <tbody>
  {% for t in tutors %}
    <tr>
      <td>{{ t.name }}</td>
      <td>{{ t.subjects }}</td>
      <td>{{ t.phone or '—' }}</td>
      <td>{{ t.windows | length }} window{{ '' if t.windows | length == 1 else 's' }}</td>
      <td><span class="status status-{{ t.status }}">{{ t.status.title() }}</span></td>
      <td class="actions">
        <a class="button" href="/tutors/{{ t.id }}/availability">Availability</a>
        <a class="button" href="/tutors/{{ t.id }}/edit">Edit</a>
        <form class="inline" method="post" action="/tutors/{{ t.id }}/status">
          <input type="hidden" name="status" value="{{ 'INACTIVE' if t.status == 'ACTIVE' else 'ACTIVE' }}">
          <button type="submit">{{ 'Deactivate' if t.status == 'ACTIVE' else 'Activate' }}</button>
        </form>
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% else %}
<p class="empty">No tutors match.</p>
{% endif %}
{% endblock %}
```

```html
<!-- app/templates/tutors/form.html -->
{% extends "base.html" %}
{% block title %}{{ 'Edit tutor' if tutor else 'Add tutor' }} — Redgum Tutoring{% endblock %}
{% block content %}
<section class="card" style="max-width: 560px;">
  <h1>{{ 'Edit tutor' if tutor else 'Add tutor' }}</h1>
  {% if errors %}
    <div class="errors">
      <strong>Please fix the following:</strong>
      <ul>{% for e in errors %}<li>{{ e }}</li>{% endfor %}</ul>
    </div>
  {% endif %}
  <form method="post" action="{{ ('/tutors/' ~ tutor.id ~ '/edit') if tutor else '/tutors/new' }}">
    <div class="field">
      <label for="name">Tutor name *</label>
      <input id="name" name="name" value="{{ form.get('name', '') }}">
    </div>
    <div class="field">
      <label for="subjects">Subjects taught *</label>
      <input id="subjects" name="subjects" value="{{ form.get('subjects', '') }}"
             placeholder="Physics 10-12, Chemistry 10-12">
    </div>
    <div class="field">
      <label for="phone">Phone</label>
      <input id="phone" name="phone" value="{{ form.get('phone', '') }}">
    </div>
    <button type="submit" class="primary">Save</button>
    <a class="button" href="/tutors">Cancel</a>
  </form>
</section>
{% endblock %}
```

- [ ] **Step 7: 修改 `app/main.py` 注册路由**

```python
from app.routers import auth, students, tutors, views
```

```python
app.include_router(tutors.router)
```

- [ ] **Step 8: 运行测试(应通过)**

```bash
uv run pytest tests/test_tutors.py -q
```

Expected: `7 passed`。

- [ ] **Step 9: 手工验证**

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s -b /tmp/rg.jar http://localhost:8000/tutors | grep -c "Tomás Ferreira"
kill %1
```

Expected: `1`(若 cookie 文件已过期,先重新登录)。

- [ ] **Step 10: 提交**

```bash
git add -A
git commit -m "feat(story-04): tutor records with subjects and deactivation"
```

---

## Task 5: 管理员维护可用时段(`story/05-availability`)

**Files:**
- Create: `app/validation.py`, `app/formatting.py`
- Create: `app/services/availability.py`, `app/routers/availability.py`, `app/templates/tutors/availability.html`, `app/templates/tutors/availability_edit.html`
- Modify: `app/templating.py`(注册 Jinja 过滤器)
- Modify: `app/main.py`(注册路由)
- Create: `tests/test_availability.py`

- [ ] **Step 1: 建分支**

```bash
git checkout -b story/05-availability story/04-tutors
```

- [ ] **Step 2: 写失败测试 `tests/test_availability.py`**

```python
from datetime import time

from app.models import AvailabilityWindow


def test_availability_page_lists_windows(admin_client, tutor_record):
    r = admin_client.get(f"/tutors/{tutor_record.id}/availability")
    assert r.status_code == 200
    assert "Tuesday" in r.text
    assert "3:30 pm" in r.text
    assert "7:00 pm" in r.text


def test_add_window(admin_client, tutor_record, db_session):
    r = admin_client.post(f"/tutors/{tutor_record.id}/availability", data={
        "day_of_week": "WEDNESDAY", "start_time": "15:30", "end_time": "18:00",
    }, follow_redirects=False)
    assert r.status_code == 303
    window = db_session.query(AvailabilityWindow).filter_by(
        tutor_id=tutor_record.id, day_of_week="WEDNESDAY").one()
    assert window.start_time == time(15, 30)
    assert window.end_time == time(18, 0)


def test_end_before_start_is_rejected(admin_client, tutor_record, db_session):
    before = db_session.query(AvailabilityWindow).count()
    r = admin_client.post(f"/tutors/{tutor_record.id}/availability", data={
        "day_of_week": "WEDNESDAY", "start_time": "18:00", "end_time": "15:30",
    })
    assert r.status_code == 400
    assert "End time must be after the start time." in r.text
    assert db_session.query(AvailabilityWindow).count() == before


def test_invalid_day_and_time_are_rejected(admin_client, tutor_record):
    r = admin_client.post(f"/tutors/{tutor_record.id}/availability", data={
        "day_of_week": "MONDAY", "start_time": "nonsense", "end_time": "18:00",
    })
    assert r.status_code == 400
    assert "Day must be one of Tuesday to Saturday." in r.text
    assert "Start time must look like 15:30." in r.text


def test_edit_window(admin_client, tutor_record, db_session):
    window = tutor_record.windows[0]
    r = admin_client.post(f"/availability/{window.id}/edit", data={
        "day_of_week": "TUESDAY", "start_time": "16:00", "end_time": "19:00",
    }, follow_redirects=False)
    assert r.status_code == 303
    db_session.refresh(window)
    assert window.start_time == time(16, 0)


def test_delete_window(admin_client, tutor_record, db_session):
    window = tutor_record.windows[0]
    r = admin_client.post(f"/availability/{window.id}/delete", follow_redirects=False)
    assert r.status_code == 303
    assert db_session.get(AvailabilityWindow, window.id) is None


def test_tutor_cannot_manage_availability(tutor_client, tutor_record):
    assert tutor_client.get(f"/tutors/{tutor_record.id}/availability").status_code == 403


def test_unknown_tutor_returns_404(admin_client):
    assert admin_client.get("/tutors/9999/availability").status_code == 404
```

- [ ] **Step 3: 运行确认失败**

```bash
uv run pytest tests/test_availability.py -q
```

Expected: 全部失败(404)。

- [ ] **Step 4: 写 `app/validation.py` 与 `app/formatting.py`**

```python
# app/validation.py
from datetime import date, datetime, time


def parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_time(value: str) -> time | None:
    try:
        return datetime.strptime(value.strip(), "%H:%M").time()
    except ValueError:
        return None
```

```python
# app/formatting.py
from datetime import date, time


def fmt_time(value: time) -> str:
    return value.strftime("%I:%M %p").lstrip("0").lower()


def fmt_date(value: date) -> str:
    return f"{value.strftime('%a')} {value.day} {value.strftime('%b %Y')}"
```

（`app/routers/_helpers.py` 已在 Task 3 创建，本任务直接使用。）

- [ ] **Step 5: 在 `app/templating.py` 注册过滤器**

在 `templates = Jinja2Templates(...)` 之后加:

```python
from app.formatting import fmt_date, fmt_time

templates.env.filters["time12"] = fmt_time
templates.env.filters["date_long"] = fmt_date
```

- [ ] **Step 6: 写 `app/services/availability.py`**

```python
from datetime import time

from sqlalchemy.orm import Session as OrmSession

from app.models import DAY_ORDER, OPEN_DAYS, AvailabilityWindow, Tutor
from app.validation import parse_time


def list_windows(tutor: Tutor) -> list[AvailabilityWindow]:
    return sorted(tutor.windows, key=lambda w: (DAY_ORDER[w.day_of_week], w.start_time))


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
    window = AvailabilityWindow(tutor_id=tutor.id, day_of_week=day_of_week,
                                start_time=start_time, end_time=end_time)
    db.add(window)
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
```

同时在 `app/models.py` 的 `OPEN_DAYS` 定义之后加:

```python
DAY_ORDER = {day: index for index, day in enumerate(OPEN_DAYS)}
```

- [ ] **Step 7: 写 `app/routers/availability.py`**

```python
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


def _page(request: Request, db: OrmSession, tutor: Tutor, form: dict, errors: list[str],
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
    return _page(request, db, tutor, {}, [])


@router.post("/tutors/{tutor_id}/availability")
def add_window(tutor_id: int, request: Request, day_of_week: str = Form(""),
               start_time: str = Form(""), end_time: str = Form(""),
               user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    tutor = get_or_404(db, Tutor, tutor_id, "Tutor")
    data, errors = availability_service.validate_window_form(day_of_week, start_time, end_time)
    if errors:
        return _page(request, db, tutor,
                     {"day_of_week": day_of_week, "start_time": start_time, "end_time": end_time},
                     errors, status_code=400)
    availability_service.add_window(db, tutor, **data)
    flash(request, f"Availability added for {tutor.name}.")
    return RedirectResponse(f"/tutors/{tutor.id}/availability", status_code=303)


@router.get("/availability/{window_id}/edit")
def edit_window_form(window_id: int, request: Request, user: AppUser = Depends(require_admin),
                     db: OrmSession = Depends(get_db)):
    window = get_or_404(db, AvailabilityWindow, window_id, "Availability window")
    form = {
        "day_of_week": window.day_of_week,
        "start_time": window.start_time.strftime("%H:%M"),
        "end_time": window.end_time.strftime("%H:%M"),
    }
    return render(request, "tutors/availability_edit.html",
                  {"window": window, "tutor": window.tutor, "form": form, "errors": []})


@router.post("/availability/{window_id}/edit")
def edit_window(window_id: int, request: Request, day_of_week: str = Form(""),
                start_time: str = Form(""), end_time: str = Form(""),
                user: AppUser = Depends(require_admin), db: OrmSession = Depends(get_db)):
    window = get_or_404(db, AvailabilityWindow, window_id, "Availability window")
    data, errors = availability_service.validate_window_form(day_of_week, start_time, end_time)
    form = {"day_of_week": day_of_week, "start_time": start_time, "end_time": end_time}
    if errors:
        return render(request, "tutors/availability_edit.html",
                      {"window": window, "tutor": window.tutor, "form": form, "errors": errors},
                      status_code=400)
    availability_service.update_window(db, window, **data)
    flash(request, "Availability updated.")
    return RedirectResponse(f"/tutors/{window.tutor_id}/availability", status_code=303)


@router.post("/availability/{window_id}/delete")
def delete_window(window_id: int, request: Request, user: AppUser = Depends(require_admin),
                  db: OrmSession = Depends(get_db)):
    window = get_or_404(db, AvailabilityWindow, window_id, "Availability window")
    tutor = window.tutor
    availability_service.delete_window(db, window)
    flash(request, "Availability removed.")
    return RedirectResponse(f"/tutors/{tutor.id}/availability", status_code=303)
```

- [ ] **Step 8: 写 `app/templates/tutors/availability.html`**

```html
{% extends "base.html" %}
{% block title %}Availability — {{ tutor.name }} — Redgum Tutoring{% endblock %}
{% block content %}
<div class="toolbar">
  <h1>Availability — {{ tutor.name }}</h1>
  <a class="button" href="/tutors">Back to tutors</a>
</div>
{% if errors %}
  <div class="errors">
    <strong>Please fix the following:</strong>
    <ul>{% for e in errors %}<li>{{ e }}</li>{% endfor %}</ul>
  </div>
{% endif %}
<section class="card">
  <h2>Current windows</h2>
  {% if windows %}
  <table>
    <thead><tr><th>Day</th><th>From</th><th>Until</th><th></th></tr></thead>
    <tbody>
    {% for w in windows %}
      <tr>
        <td>{{ w.day_of_week.title() }}</td>
        <td>{{ w.start_time | time12 }}</td>
        <td>{{ w.end_time | time12 }}</td>
        <td class="actions">
          <a class="button" href="/availability/{{ w.id }}/edit">Edit</a>
          <form class="inline" method="post" action="/availability/{{ w.id }}/delete">
            <button type="submit" class="danger">Remove</button>
          </form>
        </td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
    <p class="empty">No availability windows yet — this tutor cannot be booked.</p>
  {% endif %}
</section>
<section class="card" style="max-width: 560px;">
  <h2>Add a window</h2>
  <form method="post" action="/tutors/{{ tutor.id }}/availability">
    <div class="field">
      <label for="day_of_week">Day</label>
      <select id="day_of_week" name="day_of_week">
        {% for day in ['TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'] %}
          <option value="{{ day }}" {% if form.get('day_of_week') == day %}selected{% endif %}>{{ day.title() }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="field">
      <label for="start_time">From</label>
      <input type="time" id="start_time" name="start_time" value="{{ form.get('start_time', '') }}">
    </div>
    <div class="field">
      <label for="end_time">Until</label>
      <input type="time" id="end_time" name="end_time" value="{{ form.get('end_time', '') }}">
    </div>
    <button type="submit" class="primary">Add window</button>
  </form>
</section>
{% endblock %}
```

- [ ] **Step 8b: 写 `app/templates/tutors/availability_edit.html`(独立编辑页,避免 HTML 表格内嵌表单的非法结构)**

```html
{% extends "base.html" %}
{% block title %}Edit availability — {{ tutor.name }} — Redgum Tutoring{% endblock %}
{% block content %}
<section class="card" style="max-width: 560px;">
  <h1>Edit availability — {{ tutor.name }}</h1>
  {% if errors %}
    <div class="errors">
      <strong>Please fix the following:</strong>
      <ul>{% for e in errors %}<li>{{ e }}</li>{% endfor %}</ul>
    </div>
  {% endif %}
  <form method="post" action="/availability/{{ window.id }}/edit">
    <div class="field">
      <label for="day_of_week">Day</label>
      <select id="day_of_week" name="day_of_week">
        {% for day in ['TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'] %}
          <option value="{{ day }}" {% if form.get('day_of_week') == day %}selected{% endif %}>{{ day.title() }}</option>
        {% endfor %}
      </select>
    </div>
    <div class="field">
      <label for="start_time">From</label>
      <input type="time" id="start_time" name="start_time" value="{{ form.get('start_time', '') }}">
    </div>
    <div class="field">
      <label for="end_time">Until</label>
      <input type="time" id="end_time" name="end_time" value="{{ form.get('end_time', '') }}">
    </div>
    <button type="submit" class="primary">Save</button>
    <a class="button" href="/tutors/{{ tutor.id }}/availability">Cancel</a>
  </form>
</section>
{% endblock %}
```

- [ ] **Step 9: 修改 `app/main.py` 注册路由**

```python
from app.routers import auth, availability, students, tutors, views
```

```python
app.include_router(availability.router)
```

- [ ] **Step 10: 运行测试(应通过)**

```bash
uv run pytest tests/test_availability.py -q
```

Expected: `8 passed`。

- [ ] **Step 11: 手工验证**

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s -b /tmp/rg.jar "http://localhost:8000/tutors/1/availability" | grep -c "3:30 pm"
kill %1
```

Expected: 至少 `1`。

- [ ] **Step 12: 提交**

```bash
git add -A
git commit -m "feat(story-05): tutor availability windows with add, edit and remove"
```

---

## Task 6: 排课与可用时段校验(`story/06-book-session`)

**Files:**
- Create: `app/services/sessions.py`, `app/routers/sessions.py`, `app/templates/sessions/list.html`, `app/templates/sessions/form.html`
- Modify: `app/main.py`(注册路由)
- Create: `tests/test_availability_rule.py`, `tests/test_sessions.py`

- [ ] **Step 1: 建分支**

```bash
git checkout -b story/06-book-session story/05-availability
```

- [ ] **Step 2: 写核心规则的失败测试 `tests/test_availability_rule.py`**

```python
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
```

- [ ] **Step 3: 写排课集成的失败测试 `tests/test_sessions.py`**

```python
from datetime import time

from app.models import Session, Tutor


def test_book_a_session_inside_availability(admin_client, tutor_record, make_student, db_session):
    student = make_student()
    r = admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "Physics",
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    }, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/sessions"
    session = db_session.query(Session).one()
    assert session.status == "BOOKED"
    assert session.start_time == time(16, 0)


def test_booking_outside_availability_is_refused(admin_client, tutor_record, make_student, db_session):
    student = make_student()
    r = admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "Physics",
        "session_date": "2026-08-11", "start_time": "18:30", "length_minutes": "60",
    })
    assert r.status_code == 400
    assert "would not fit" in r.text
    assert db_session.query(Session).count() == 0


def test_deactivated_tutor_is_not_offered_and_cannot_be_booked(admin_client, tutor_record, make_student, db_session):
    tutor_record.status = "INACTIVE"
    db_session.commit()
    student = make_student()

    form = admin_client.get("/sessions/new")
    assert "Tomás Ferreira" not in form.text

    r = admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "Physics",
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    })
    assert r.status_code == 400
    assert "not an active tutor" in r.text


def test_inactive_student_cannot_be_booked(admin_client, tutor_record, make_student):
    student = make_student(status="INACTIVE")
    r = admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "Physics",
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    })
    assert r.status_code == 400
    assert "not an active student" in r.text


def test_required_fields_are_reported(admin_client, db_session):
    r = admin_client.post("/sessions/new", data={
        "student_id": "", "tutor_id": "", "subject": "", "session_date": "", "start_time": "",
        "length_minutes": "45",
    })
    assert r.status_code == 400
    assert "Choose a student." in r.text
    assert "Choose a tutor." in r.text
    assert "Subject is required." in r.text
    assert "Date must look like 2026-08-11." in r.text
    assert "Start time must look like 15:30." in r.text
    assert "Length must be 60 or 90 minutes." in r.text
    assert db_session.query(Session).count() == 0


def test_booked_session_appears_in_the_list(admin_client, tutor_record, make_student):
    student = make_student()
    admin_client.post("/sessions/new", data={
        "student_id": str(student.id), "tutor_id": str(tutor_record.id), "subject": "Physics",
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    })
    r = admin_client.get("/sessions")
    assert "Ella Nguyen" in r.text
    assert "Tomás Ferreira" in r.text
    assert "Physics" in r.text


def test_tutor_cannot_book_sessions(tutor_client):
    assert tutor_client.get("/sessions").status_code == 403
    assert tutor_client.get("/sessions/new").status_code == 403
```

- [ ] **Step 4: 运行确认失败**

```bash
uv run pytest tests/test_availability_rule.py tests/test_sessions.py -q
```

Expected: 失败(`app.services.sessions` 不存在 → 导入错误;HTTP 404)。

- [ ] **Step 5: 写 `app/services/sessions.py`(本任务部分:规则 + 排课 + 列表)**

```python
from datetime import date, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.errors import DomainError
from app.formatting import fmt_time
from app.models import DAY_NAMES, SESSION_LENGTHS, SESSION_STATUSES, Session, Student, Tutor


def session_end_time(start_time: time, length_minutes: int) -> time:
    anchor = datetime(2000, 1, 1, start_time.hour, start_time.minute)
    return (anchor + timedelta(minutes=length_minutes)).time()


def validate_slot(tutor: Tutor, session_date: date, start_time: time, length_minutes: int) -> None:
    """The centre's operating rule: a session must fit entirely inside one availability window."""
    if length_minutes not in SESSION_LENGTHS:
        raise DomainError("Sessions are 60 or 90 minutes long.")
    if tutor.status != "ACTIVE":
        raise DomainError(f"{tutor.name} is not an active tutor.")
    day = DAY_NAMES[session_date.weekday()]
    windows = [w for w in tutor.windows if w.day_of_week == day]
    if not windows:
        raise DomainError(f"{tutor.name} has no availability on {day.title()}.")
    end_time = session_end_time(start_time, length_minutes)
    for window in windows:
        if window.start_time <= start_time and end_time <= window.end_time:
            return
    listed = ", ".join(f"{fmt_time(w.start_time)}–{fmt_time(w.end_time)}"
                       for w in sorted(windows, key=lambda w: w.start_time))
    raise DomainError(
        f"{tutor.name} is only available on {day.title()} {listed}; "
        f"a {length_minutes}-minute session starting at {fmt_time(start_time)} would not fit."
    )


def book_session(db: OrmSession, *, student: Student, tutor: Tutor, subject: str, session_date: date,
                 start_time: time, length_minutes: int) -> Session:
    if student.status != "ACTIVE":
        raise DomainError(f"{student.name} is not an active student.")
    validate_slot(tutor, session_date, start_time, length_minutes)
    session = Session(student_id=student.id, tutor_id=tutor.id, subject=subject,
                      session_date=session_date, start_time=start_time,
                      length_minutes=length_minutes, status="BOOKED")
    db.add(session)
    db.commit()
    return session


def list_sessions(db: OrmSession, *, date_from: date | None = None, date_to: date | None = None,
                  tutor_id: int | None = None, student_id: int | None = None,
                  status: str = "") -> list[Session]:
    stmt = select(Session)
    if date_from is not None:
        stmt = stmt.where(Session.session_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Session.session_date <= date_to)
    if tutor_id is not None:
        stmt = stmt.where(Session.tutor_id == tutor_id)
    if student_id is not None:
        stmt = stmt.where(Session.student_id == student_id)
    if status in SESSION_STATUSES:
        stmt = stmt.where(Session.status == status)
    return list(db.scalars(stmt.order_by(Session.session_date, Session.start_time)))
```

- [ ] **Step 6: 写 `app/routers/sessions.py`(本任务部分:列表 + 排课)**

```python
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.errors import DomainError
from app.models import AppUser, SESSION_LENGTHS, Student, Tutor
from app.security import require_admin
from app.services import sessions as session_service
from app.services import students as student_service
from app.services import tutors as tutor_service
from app.templating import flash, render
from app.validation import parse_date, parse_time

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _form_context(db: OrmSession, session, form: dict, errors: list[str]) -> dict:
    return {
        "session": session,
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
    return render(request, "sessions/form.html", _form_context(db, None, {"length_minutes": "60"}, []))


@router.post("/new")
def create(request: Request, student_id: str = Form(""), tutor_id: str = Form(""),
           subject: str = Form(""), session_date: str = Form(""), start_time: str = Form(""),
           length_minutes: str = Form(""), user: AppUser = Depends(require_admin),
           db: OrmSession = Depends(get_db)):
    form = {"student_id": student_id, "tutor_id": tutor_id, "subject": subject,
            "session_date": session_date, "start_time": start_time, "length_minutes": length_minutes}
    errors: list[str] = []

    student = db.get(Student, int(student_id)) if student_id.isdigit() else None
    if student is None:
        errors.append("Choose a student.")
    tutor = db.get(Tutor, int(tutor_id)) if tutor_id.isdigit() else None
    if tutor is None:
        errors.append("Choose a tutor.")

    subject = subject.strip()
    if not subject:
        errors.append("Subject is required.")

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
            session_service.book_session(db, student=student, tutor=tutor, subject=subject,
                                         session_date=parsed_date, start_time=parsed_start,
                                         length_minutes=length)
        except DomainError as exc:
            errors.append(exc.message)

    if errors:
        return render(request, "sessions/form.html", _form_context(db, None, form, errors),
                      status_code=400)
    flash(request, "Session booked.")
    return RedirectResponse("/sessions", status_code=303)
```

- [ ] **Step 7: 写 `app/templates/sessions/list.html` 与 `app/templates/sessions/form.html`**

```html
<!-- app/templates/sessions/list.html -->
{% extends "base.html" %}
{% block title %}Sessions — Redgum Tutoring{% endblock %}
{% block content %}
<div class="toolbar">
  <h1>Sessions</h1>
  <a class="button primary" href="/sessions/new">Book session</a>
</div>
<form method="get" action="/sessions" class="filters card">
  <div class="field" style="margin:0">
    <label for="date_from">From</label>
    <input type="date" id="date_from" name="date_from" value="{{ filters.date_from }}">
  </div>
  <div class="field" style="margin:0">
    <label for="date_to">To</label>
    <input type="date" id="date_to" name="date_to" value="{{ filters.date_to }}">
  </div>
  <div class="field" style="margin:0">
    <label for="tutor_id">Tutor</label>
    <select id="tutor_id" name="tutor_id">
      <option value="">All</option>
      {% for t in tutors %}
        <option value="{{ t.id }}" {% if filters.tutor_id == t.id | string %}selected{% endif %}>{{ t.name }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="field" style="margin:0">
    <label for="student_id">Student</label>
    <select id="student_id" name="student_id">
      <option value="">All</option>
      {% for s in students %}
        <option value="{{ s.id }}" {% if filters.student_id == s.id | string %}selected{% endif %}>{{ s.name }}</option>
      {% endfor %}
    </select>
  </div>
  <div class="field" style="margin:0">
    <label for="status">Status</label>
    <select id="status" name="status">
      <option value="">All</option>
      {% for value in ['BOOKED', 'ATTENDED', 'CANCELLED', 'MISSED'] %}
        <option value="{{ value }}" {% if filters.status == value %}selected{% endif %}>{{ value.title() }}</option>
      {% endfor %}
    </select>
  </div>
  <button type="submit">Filter</button>
</form>
{% if sessions %}
<table>
  <thead>
    <tr><th>Date</th><th>Time</th><th>Length</th><th>Student</th><th>Tutor</th><th>Subject</th><th>Status</th><th></th></tr>
  </thead>
  <tbody>
  {% for s in sessions %}
    <tr>
      <td>{{ s.session_date | date_long }}</td>
      <td>{{ s.start_time | time12 }}</td>
      <td>{{ s.length_minutes }} min</td>
      <td>{{ s.student.name }}</td>
      <td>{{ s.tutor.name }}</td>
      <td>{{ s.subject }}</td>
      <td><span class="status status-{{ s.status }}">{{ s.status.title() }}</span></td>
      <td class="actions">
        {% if s.status == 'BOOKED' %}
          <a class="button" href="/sessions/{{ s.id }}/edit">Move</a>
          <form class="inline" method="post" action="/sessions/{{ s.id }}/status">
            <input type="hidden" name="outcome" value="ATTENDED">
            <button type="submit">Attended</button>
          </form>
          <form class="inline" method="post" action="/sessions/{{ s.id }}/status">
            <input type="hidden" name="outcome" value="MISSED">
            <button type="submit">Missed</button>
          </form>
          <form class="inline" method="post" action="/sessions/{{ s.id }}/cancel">
            <button type="submit" class="danger">Cancel</button>
          </form>
        {% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody>
</table>
{% else %}
<p class="empty">No sessions match.</p>
{% endif %}
{% endblock %}
```

```html
<!-- app/templates/sessions/form.html -->
{% extends "base.html" %}
{% block title %}Book session — Redgum Tutoring{% endblock %}
{% block content %}
<section class="card" style="max-width: 560px;">
  <h1>Book session</h1>
  {% if errors %}
    <div class="errors">
      <strong>Please fix the following:</strong>
      <ul>{% for e in errors %}<li>{{ e }}</li>{% endfor %}</ul>
    </div>
  {% endif %}
  <form method="post" action="/sessions/new">
    <div class="field">
      <label for="student_id">Student *</label>
      <select id="student_id" name="student_id">
        <option value="">Choose…</option>
        {% for s in students %}
          <option value="{{ s.id }}" {% if form.get('student_id') == s.id | string %}selected{% endif %}>
            {{ s.name }} (Year {{ s.year_level }})
          </option>
        {% endfor %}
      </select>
    </div>
    <div class="field">
      <label for="tutor_id">Tutor *</label>
      <select id="tutor_id" name="tutor_id">
        <option value="">Choose…</option>
        {% for t in tutors %}
          <option value="{{ t.id }}" {% if form.get('tutor_id') == t.id | string %}selected{% endif %}>
            {{ t.name }} — {{ t.subjects }}
          </option>
        {% endfor %}
      </select>
    </div>
    <div class="field">
      <label for="subject">Subject *</label>
      <input id="subject" name="subject" value="{{ form.get('subject', '') }}" placeholder="Physics">
    </div>
    <div class="field">
      <label for="session_date">Date *</label>
      <input type="date" id="session_date" name="session_date" value="{{ form.get('session_date', '') }}">
    </div>
    <div class="field">
      <label for="start_time">Start time *</label>
      <input type="time" id="start_time" name="start_time" value="{{ form.get('start_time', '') }}">
      <div class="hint">The session must fit entirely inside one of the tutor's availability windows for that day.</div>
    </div>
    <div class="field">
      <label for="length_minutes">Length *</label>
      <select id="length_minutes" name="length_minutes">
        <option value="60" {% if form.get('length_minutes', '60') == '60' %}selected{% endif %}>60 minutes</option>
        <option value="90" {% if form.get('length_minutes') == '90' %}selected{% endif %}>90 minutes</option>
      </select>
    </div>
    <button type="submit" class="primary">Book session</button>
    <a class="button" href="/sessions">Cancel</a>
  </form>
</section>
{% endblock %}
```

- [ ] **Step 8: 修改 `app/main.py` 注册路由**

```python
from app.routers import auth, availability, sessions, students, tutors, views
```

```python
app.include_router(sessions.router)
```

- [ ] **Step 9: 运行测试(应通过)**

```bash
uv run pytest tests/test_availability_rule.py tests/test_sessions.py -q
```

Expected: `10 passed`(规则)+ `7 passed`(排课)。

- [ ] **Step 10: 手工验证核心规则**

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 3
# Tomás 周二窗口 15:30–19:00;18:30 开始 60 分钟应当被拒绝
curl -s -b /tmp/rg.jar -X POST http://localhost:8000/sessions/new \
  -d "student_id=1&tutor_id=1&subject=Physics&session_date=2026-08-11&start_time=18:30&length_minutes=60" \
  | grep -o "would not fit" | head -1
# 16:00 应当成功
curl -s -o /dev/null -w "%{http_code}\n" -b /tmp/rg.jar -X POST http://localhost:8000/sessions/new \
  -d "student_id=1&tutor_id=1&subject=Physics&session_date=2026-08-11&start_time=16:00&length_minutes=60"
kill %1
```

Expected: 第一行输出 `would not fit`;第二行 `303`。

- [ ] **Step 11: 提交**

```bash
git add -A
git commit -m "feat(story-06): session booking with the tutor availability rule"
```

---

## Task 7: 改期、取消与状态流转(`story/07-manage-session`)

**Files:**
- Modify: `app/services/sessions.py`(加 `move_session`、`cancel_session`、`set_outcome`)
- Modify: `app/routers/sessions.py`(加 edit/cancel/status 路由)
- Create: `app/templates/sessions/edit.html`
- Modify: `tests/test_sessions.py`(追加)

- [ ] **Step 1: 建分支**

```bash
git checkout -b story/07-manage-session story/06-book-session
```

- [ ] **Step 2: 追加失败测试到 `tests/test_sessions.py`**

```python
def test_move_a_session_within_availability(admin_client, tutor_record, make_student, make_session, db_session):
    session = make_session(make_student(), tutor_record, session_date=date(2026, 8, 11), start_time=time(15, 30))
    r = admin_client.post(f"/sessions/{session.id}/edit", data={
        "session_date": "2026-08-11", "start_time": "17:00", "length_minutes": "60",
    }, follow_redirects=False)
    assert r.status_code == 303
    db_session.refresh(session)
    assert session.start_time == time(17, 0)


def test_move_outside_availability_is_refused_and_nothing_changes(admin_client, tutor_record, make_student, make_session, db_session):
    session = make_session(make_student(), tutor_record, session_date=date(2026, 8, 11), start_time=time(15, 30))
    r = admin_client.post(f"/sessions/{session.id}/edit", data={
        "session_date": "2026-08-11", "start_time": "18:30", "length_minutes": "60",
    })
    assert r.status_code == 400
    assert "would not fit" in r.text
    db_session.refresh(session)
    assert session.start_time == time(15, 30)


def test_cancel_a_session_keeps_it_visible(admin_client, tutor_record, make_student, make_session, db_session):
    session = make_session(make_student(), tutor_record)
    r = admin_client.post(f"/sessions/{session.id}/cancel", follow_redirects=False)
    assert r.status_code == 303
    db_session.refresh(session)
    assert session.status == "CANCELLED"
    listing = admin_client.get("/sessions")
    assert "Cancelled" in listing.text


def test_mark_attended_and_missed(admin_client, tutor_record, make_student, make_session, db_session):
    attended = make_session(make_student(), tutor_record, start_time=time(15, 30))
    missed = make_session(make_student(name="Kai Lombardo"), tutor_record, start_time=time(16, 30))

    admin_client.post(f"/sessions/{attended.id}/status", data={"outcome": "ATTENDED"})
    admin_client.post(f"/sessions/{missed.id}/status", data={"outcome": "MISSED"})

    db_session.refresh(attended)
    db_session.refresh(missed)
    assert attended.status == "ATTENDED"
    assert missed.status == "MISSED"


def test_a_finished_session_cannot_be_moved_or_cancelled(admin_client, tutor_record, make_student, make_session):
    session = make_session(make_student(), tutor_record, status="CANCELLED")
    moved = admin_client.post(f"/sessions/{session.id}/edit", data={
        "session_date": "2026-08-11", "start_time": "17:00", "length_minutes": "60",
    })
    assert moved.status_code == 400
    assert "Only booked sessions can be moved." in moved.text
    cancelled = admin_client.post(f"/sessions/{session.id}/cancel")
    assert cancelled.status_code == 400
    assert "Only booked sessions can be cancelled." in cancelled.text


def test_moving_one_session_does_not_affect_another(admin_client, tutor_record, make_student, make_session, db_session):
    student = make_student()
    first = make_session(student, tutor_record, start_time=time(15, 30))
    second = make_session(student, tutor_record, start_time=time(17, 0))

    admin_client.post(f"/sessions/{first.id}/edit", data={
        "session_date": "2026-08-11", "start_time": "16:00", "length_minutes": "60",
    })

    db_session.refresh(first)
    db_session.refresh(second)
    assert first.start_time == time(16, 0)
    assert second.start_time == time(17, 0)


def test_tutor_cannot_change_sessions(tutor_client, tutor_record, make_student, make_session):
    session = make_session(make_student(), tutor_record)
    assert tutor_client.post(f"/sessions/{session.id}/cancel").status_code == 403
    assert tutor_client.get(f"/sessions/{session.id}/edit").status_code == 403
```

同时在文件头补 import:

```python
from datetime import date, time
```

- [ ] **Step 3: 运行确认失败**

```bash
uv run pytest tests/test_sessions.py -q
```

Expected: 新增的 7 个测试失败(404/405)。

- [ ] **Step 4: 在 `app/services/sessions.py` 追加三个方法**

```python
def move_session(db: OrmSession, session: Session, *, session_date: date, start_time: time,
                 length_minutes: int) -> Session:
    if session.status != "BOOKED":
        raise DomainError("Only booked sessions can be moved.")
    validate_slot(session.tutor, session_date, start_time, length_minutes)
    session.session_date = session_date
    session.start_time = start_time
    session.length_minutes = length_minutes
    db.commit()
    return session


def cancel_session(db: OrmSession, session: Session) -> Session:
    if session.status != "BOOKED":
        raise DomainError("Only booked sessions can be cancelled.")
    session.status = "CANCELLED"
    db.commit()
    return session


def set_outcome(db: OrmSession, session: Session, outcome: str) -> Session:
    if session.status != "BOOKED":
        raise DomainError("Only booked sessions can be marked.")
    if outcome not in ("ATTENDED", "MISSED"):
        raise DomainError("Outcome must be attended or missed.")
    session.status = outcome
    db.commit()
    return session
```

- [ ] **Step 5: 在 `app/routers/sessions.py` 追加路由**

```python
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
```

同时补 import:

```python
from app.models import AppUser, SESSION_LENGTHS, Session, Student, Tutor
from app.routers._helpers import get_or_404
```

注意:`cancel`/`status` 用 flash 而不是 400 表单——它们是列表页的一键操作,失败时回列表并显示原因更自然;`edit` 是表单,失败回表单显示错误。

- [ ] **Step 6: 写 `app/templates/sessions/edit.html`**

```html
{% extends "base.html" %}
{% block title %}Move session — Redgum Tutoring{% endblock %}
{% block content %}
<section class="card" style="max-width: 560px;">
  <h1>Move session</h1>
  <p class="muted">
    {{ session.student.name }} with {{ session.tutor.name }} — {{ session.subject }}
    ({{ session.length_minutes }} minutes)
  </p>
  {% if errors %}
    <div class="errors">
      <strong>Please fix the following:</strong>
      <ul>{% for e in errors %}<li>{{ e }}</li>{% endfor %}</ul>
    </div>
  {% endif %}
  <form method="post" action="/sessions/{{ session.id }}/edit">
    <div class="field">
      <label for="session_date">Date *</label>
      <input type="date" id="session_date" name="session_date" value="{{ form.get('session_date', '') }}">
    </div>
    <div class="field">
      <label for="start_time">Start time *</label>
      <input type="time" id="start_time" name="start_time" value="{{ form.get('start_time', '') }}">
      <div class="hint">The new time must fit entirely inside one of {{ session.tutor.name }}'s availability windows.</div>
    </div>
    <div class="field">
      <label for="length_minutes">Length *</label>
      <select id="length_minutes" name="length_minutes">
        <option value="60" {% if form.get('length_minutes') == '60' %}selected{% endif %}>60 minutes</option>
        <option value="90" {% if form.get('length_minutes') == '90' %}selected{% endif %}>90 minutes</option>
      </select>
    </div>
    <button type="submit" class="primary">Save changes</button>
    <a class="button" href="/sessions">Cancel</a>
  </form>
</section>
{% endblock %}
```

- [ ] **Step 7: 运行测试(应通过)**

```bash
uv run pytest tests/test_sessions.py tests/test_availability_rule.py -q
```

Expected: `14 passed`(sessions)+ `10 passed`(rule)。

- [ ] **Step 8: 手工验证**

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s -b /tmp/rg.jar http://localhost:8000/sessions | grep -c "Cancelled"
kill %1
```

Expected: 至少 `1`(种子数据里有两节已取消的课)。

- [ ] **Step 9: 提交**

```bash
git add -A
git commit -m "feat(story-07): move, cancel and mark sessions with availability re-checks"
```

---

## Task 8: 课表与学生历史(`story/08-schedule`)

**Files:**
- Create: `app/services/schedule.py`, `app/templates/schedule.html`, `app/templates/students/sessions.html`
- Modify: `app/routers/views.py`(加 `/schedule`)、`app/routers/students.py`(加 `/students/{id}/sessions`)、`app/templates/students/list.html`(加 Sessions 链接)
- Create: `tests/test_schedule.py`

- [ ] **Step 1: 建分支**

```bash
git checkout -b story/08-schedule story/07-manage-session
```

- [ ] **Step 2: 写失败测试 `tests/test_schedule.py`**

```python
from datetime import date, timedelta, time


def test_day_view_shows_only_that_day(admin_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2026, 8, 11), start_time=time(15, 30))
    make_session(student, tutor_record, session_date=date(2026, 8, 13), start_time=time(16, 0))

    r = admin_client.get("/schedule?view=day&date=2026-08-11")
    assert r.status_code == 200
    assert "Tue 11 Aug 2026" in r.text
    assert "Thu 13 Aug 2026" not in r.text


def test_week_view_covers_tuesday_to_saturday(admin_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2026, 8, 15), start_time=time(9, 0))

    r = admin_client.get("/schedule?view=week&date=2026-08-13")
    assert r.status_code == 200
    for label in ["Tue 11 Aug 2026", "Wed 12 Aug 2026", "Thu 13 Aug 2026",
                  "Fri 14 Aug 2026", "Sat 15 Aug 2026"]:
        assert label in r.text
    assert "Ella Nguyen" in r.text


def test_schedule_can_be_filtered_by_tutor(admin_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2026, 8, 11), start_time=time(15, 30))

    r = admin_client.get(f"/schedule?view=week&date=2026-08-11&tutor_id={tutor_record.id}")
    assert "Ella Nguyen" in r.text

    r = admin_client.get("/schedule?view=week&date=2026-08-11&tutor_id=9999")
    assert "Ella Nguyen" not in r.text


def test_empty_day_shows_a_clear_message(admin_client):
    r = admin_client.get("/schedule?view=day&date=2026-08-11")
    assert r.status_code == 200
    assert "No sessions." in r.text


def test_student_history_lists_past_and_future(admin_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2026, 8, 11), start_time=time(15, 30), status="ATTENDED")
    make_session(student, tutor_record, session_date=date.today() + timedelta(days=7), start_time=time(15, 30))

    r = admin_client.get(f"/students/{student.id}/sessions")
    assert r.status_code == 200
    assert "Upcoming" in r.text
    assert "Past" in r.text
    assert "Tue 11 Aug 2026" in r.text
    assert "No upcoming sessions." not in r.text


def test_tutor_cannot_see_the_schedule(tutor_client):
    assert tutor_client.get("/schedule").status_code == 403
```

- [ ] **Step 3: 运行确认失败**

```bash
uv run pytest tests/test_schedule.py -q
```

Expected: 全部失败(404)。

- [ ] **Step 4: 写 `app/services/schedule.py`**

```python
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session as OrmSession

from app.models import Session


def week_start(value: date) -> date:
    """Tuesday of the centre week that contains the given date."""
    return value - timedelta(days=(value.weekday() - 1) % 7)


def sessions_between(db: OrmSession, start: date, end: date,
                     tutor_id: int | None = None) -> list[Session]:
    stmt = select(Session).where(Session.session_date >= start, Session.session_date <= end)
    if tutor_id is not None:
        stmt = stmt.where(Session.tutor_id == tutor_id)
    return list(db.scalars(stmt.order_by(Session.session_date, Session.start_time)))


def week_days(week_start_date: date) -> list[date]:
    """Tuesday to Saturday."""
    return [week_start_date + timedelta(days=offset) for offset in range(5)]


def sessions_on(sessions: list[Session], day: date) -> list[Session]:
    return [s for s in sessions if s.session_date == day]


def student_sessions(db: OrmSession, student_id: int, today: date) -> tuple[list[Session], list[Session]]:
    sessions = list(db.scalars(select(Session)
                               .where(Session.student_id == student_id)
                               .order_by(Session.session_date, Session.start_time)))
    past = [s for s in sessions if s.session_date < today]
    future = [s for s in sessions if s.session_date >= today]
    return past, future
```

- [ ] **Step 5: 在 `app/routers/views.py` 加 `/schedule`(整文件替换)**

```python
from datetime import date

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as OrmSession

from app.db import get_db
from app.models import AppUser, Tutor
from app.security import require_admin, require_user
from app.services import schedule as schedule_service
from app.services import tutors as tutor_service
from app.templating import render
from app.validation import parse_date

router = APIRouter(tags=["views"])


@router.get("/")
def home(user: AppUser = Depends(require_user)):
    if user.role == "ADMIN":
        return RedirectResponse("/students", status_code=303)
    return RedirectResponse("/my-sessions", status_code=303)


@router.get("/schedule")
def schedule(request: Request, start: str = Query("", alias="date"), view: str = "week",
             tutor_id: str = "", user: AppUser = Depends(require_admin),
             db: OrmSession = Depends(get_db)):
    anchor = parse_date(start) or date.today()
    tutor_filter = int(tutor_id) if tutor_id.isdigit() else None
    tutor_filter_id = tutor_filter or ""

    if view == "day":
        sessions = schedule_service.sessions_between(db, anchor, anchor, tutor_filter)
        days = [(anchor, sessions)]
    else:
        range_start = schedule_service.week_start(anchor)
        sessions = schedule_service.sessions_between(
            db, range_start, schedule_service.week_days(range_start)[-1], tutor_filter)
        days = [(day, schedule_service.sessions_on(sessions, day))
                for day in schedule_service.week_days(range_start)]

    return render(request, "schedule.html", {
        "days": days,
        "view": "day" if view == "day" else "week",
        "anchor_iso": anchor.isoformat(),
        "tutor_id": tutor_filter_id,
        "tutors": tutor_service.list_tutors(db),
    })
```

- [ ] **Step 6: 在 `app/routers/students.py` 加学生历史路由,并给列表加链接**

在文件头补 import:

```python
from datetime import date

from app.routers._helpers import get_or_404
from app.services import schedule as schedule_service
```

在 `set_status` 路由之后加:

```python
@router.get("/{student_id}/sessions")
def sessions_view(student_id: int, request: Request, user: AppUser = Depends(require_admin),
                  db: OrmSession = Depends(get_db)):
    student = get_or_404(db, Student, student_id, "Student")
    past, future = schedule_service.student_sessions(db, student_id, date.today())
    return render(request, "students/sessions.html",
                  {"student": student, "past": past, "future": future})
```

在 `app/templates/students/list.html` 的 actions 单元格里,`<a class="button" href="/students/{{ s.id }}/edit">Edit</a>` 之前加:

```html
        <a class="button" href="/students/{{ s.id }}/sessions">Sessions</a>
```

- [ ] **Step 7: 写 `app/templates/schedule.html` 与 `app/templates/students/sessions.html`**

```html
<!-- app/templates/schedule.html -->
{% extends "base.html" %}
{% block title %}Schedule — Redgum Tutoring{% endblock %}
{% block content %}
<div class="toolbar">
  <h1>Schedule</h1>
  <div class="filters">
    <a class="button {% if view == 'day' %}primary{% endif %}"
       href="/schedule?view=day&date={{ anchor_iso }}{% if tutor_id %}&tutor_id={{ tutor_id }}{% endif %}">Day</a>
    <a class="button {% if view == 'week' %}primary{% endif %}"
       href="/schedule?view=week&date={{ anchor_iso }}{% if tutor_id %}&tutor_id={{ tutor_id }}{% endif %}">Week</a>
  </div>
</div>
<form method="get" action="/schedule" class="filters card">
  <input type="hidden" name="view" value="{{ view }}">
  <div class="field" style="margin:0">
    <label for="date">Date</label>
    <input type="date" id="date" name="date" value="{{ anchor_iso }}">
  </div>
  <div class="field" style="margin:0">
    <label for="tutor_id">Tutor</label>
    <select id="tutor_id" name="tutor_id">
      <option value="">All tutors</option>
      {% for t in tutors %}
        <option value="{{ t.id }}" {% if tutor_id == t.id | string %}selected{% endif %}>{{ t.name }}</option>
      {% endfor %}
    </select>
  </div>
  <button type="submit">Show</button>
</form>
{% for day, day_sessions in days %}
  <section class="card">
    <h2>{{ day | date_long }}</h2>
    {% if day_sessions %}
      <table>
        <thead><tr><th>Time</th><th>Length</th><th>Student</th><th>Tutor</th><th>Subject</th><th>Status</th></tr></thead>
        <tbody>
        {% for s in day_sessions %}
          <tr>
            <td>{{ s.start_time | time12 }}</td>
            <td>{{ s.length_minutes }} min</td>
            <td>{{ s.student.name }}</td>
            <td>{{ s.tutor.name }}</td>
            <td>{{ s.subject }}</td>
            <td><span class="status status-{{ s.status }}">{{ s.status.title() }}</span></td>
          </tr>
        {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p class="empty">No sessions.</p>
    {% endif %}
  </section>
{% endfor %}
{% endblock %}
```

```html
<!-- app/templates/students/sessions.html -->
{% extends "base.html" %}
{% block title %}{{ student.name }} — sessions — Redgum Tutoring{% endblock %}
{% block content %}
<div class="toolbar">
  <h1>{{ student.name }} — sessions</h1>
  <a class="button" href="/students">Back to students</a>
</div>
<section class="card">
  <h2>Upcoming</h2>
  {% if future %}
    <table>
      <thead><tr><th>Date</th><th>Time</th><th>Length</th><th>Tutor</th><th>Subject</th><th>Status</th></tr></thead>
      <tbody>
      {% for s in future %}
        <tr>
          <td>{{ s.session_date | date_long }}</td>
          <td>{{ s.start_time | time12 }}</td>
          <td>{{ s.length_minutes }} min</td>
          <td>{{ s.tutor.name }}</td>
          <td>{{ s.subject }}</td>
          <td><span class="status status-{{ s.status }}">{{ s.status.title() }}</span></td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p class="empty">No upcoming sessions.</p>
  {% endif %}
</section>
<section class="card">
  <h2>Past</h2>
  {% if past %}
    <table>
      <thead><tr><th>Date</th><th>Time</th><th>Length</th><th>Tutor</th><th>Subject</th><th>Status</th></tr></thead>
      <tbody>
      {% for s in past %}
        <tr>
          <td>{{ s.session_date | date_long }}</td>
          <td>{{ s.start_time | time12 }}</td>
          <td>{{ s.length_minutes }} min</td>
          <td>{{ s.tutor.name }}</td>
          <td>{{ s.subject }}</td>
          <td><span class="status status-{{ s.status }}">{{ s.status.title() }}</span></td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p class="empty">No past sessions.</p>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 8: 运行测试(应通过)**

```bash
uv run pytest tests/test_schedule.py -q
```

Expected: `6 passed`。

- [ ] **Step 9: 手工验证**

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s -b /tmp/rg.jar "http://localhost:8000/schedule?view=week" | grep -c "Ella Nguyen"
kill %1
```

Expected: 至少 `1`。

- [ ] **Step 10: 提交**

```bash
git add -A
git commit -m "feat(story-08): day and week schedule plus student session history"
```

---

## Task 9: 导师视图(`story/09-tutor-view`)

**Files:**
- Modify: `app/services/schedule.py`(加 `upcoming_for_tutor`)
- Modify: `app/routers/views.py`(加 `/my-sessions`)
- Create: `app/templates/my_sessions.html`
- Create: `tests/test_tutor_view.py`

- [ ] **Step 1: 建分支**

```bash
git checkout -b story/09-tutor-view story/08-schedule
```

- [ ] **Step 2: 写失败测试 `tests/test_tutor_view.py`**

```python
from datetime import date, time

from app.models import Tutor


def test_tutor_sees_own_upcoming_sessions(tutor_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2099, 1, 5), start_time=time(16, 0), subject="Physics")

    r = tutor_client.get("/my-sessions")
    assert r.status_code == 200
    assert "Ella Nguyen" in r.text
    assert "Physics" in r.text


def test_tutor_does_not_see_another_tutors_sessions(tutor_client, db_session, make_student, make_session):
    other = Tutor(name="Priyanka Shah", subjects="Maths 5-10", status="ACTIVE")
    db_session.add(other)
    db_session.commit()
    student = make_student()
    make_session(student, other, session_date=date(2099, 1, 5), start_time=time(16, 0), subject="Maths")

    r = tutor_client.get("/my-sessions")
    assert r.status_code == 200
    assert "Priyanka Shah" not in r.text
    assert "No upcoming sessions." in r.text


def test_tutor_with_no_sessions_gets_an_empty_list(tutor_client):
    r = tutor_client.get("/my-sessions")
    assert r.status_code == 200
    assert "No upcoming sessions." in r.text


def test_past_and_cancelled_sessions_are_not_upcoming(tutor_client, tutor_record, make_student, make_session):
    student = make_student()
    make_session(student, tutor_record, session_date=date(2020, 1, 7), start_time=time(16, 0))
    make_session(student, tutor_record, session_date=date(2099, 1, 5), start_time=time(16, 0), status="CANCELLED")

    r = tutor_client.get("/my-sessions")
    assert "No upcoming sessions." in r.text


def test_anonymous_visitor_is_redirected_to_login(client):
    r = client.get("/my-sessions", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"


def test_tutor_cannot_open_admin_pages(tutor_client):
    assert tutor_client.get("/schedule").status_code == 403
    assert tutor_client.get("/students").status_code == 403
```

- [ ] **Step 3: 运行确认失败**

```bash
uv run pytest tests/test_tutor_view.py -q
```

Expected: 失败(`/my-sessions` 404)。

- [ ] **Step 4: 在 `app/services/schedule.py` 追加 `upcoming_for_tutor`**

```python
def upcoming_for_tutor(db: OrmSession, tutor_id: int, today: date) -> list[Session]:
    return list(db.scalars(select(Session)
                           .where(Session.tutor_id == tutor_id,
                                  Session.session_date >= today,
                                  Session.status == "BOOKED")
                           .order_by(Session.session_date, Session.start_time)))
```

- [ ] **Step 5: 在 `app/routers/views.py` 追加 `/my-sessions`**

在 import 处补 `from app.models import AppUser, Tutor`(已导入 `Tutor`,确认存在),并追加:

```python
@router.get("/my-sessions")
def my_sessions(request: Request, user: AppUser = Depends(require_user),
                db: OrmSession = Depends(get_db)):
    if user.tutor_id is None:
        return render(request, "my_sessions.html", {"tutor": None, "sessions": []})
    tutor = db.get(Tutor, user.tutor_id)
    sessions = schedule_service.upcoming_for_tutor(db, tutor.id, date.today())
    return render(request, "my_sessions.html", {"tutor": tutor, "sessions": sessions})
```

- [ ] **Step 6: 写 `app/templates/my_sessions.html`**

```html
{% extends "base.html" %}
{% block title %}My sessions — Redgum Tutoring{% endblock %}
{% block content %}
<div class="toolbar">
  <h1>My sessions{% if tutor %} — {{ tutor.name }}{% endif %}</h1>
</div>
<section class="card">
  {% if sessions %}
    <table>
      <thead><tr><th>Date</th><th>Time</th><th>Length</th><th>Student</th><th>Subject</th></tr></thead>
      <tbody>
      {% for s in sessions %}
        <tr>
          <td>{{ s.session_date | date_long }}</td>
          <td>{{ s.start_time | time12 }}</td>
          <td>{{ s.length_minutes }} min</td>
          <td>{{ s.student.name }}</td>
          <td>{{ s.subject }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  {% else %}
    <p class="empty">No upcoming sessions.</p>
  {% endif %}
</section>
{% endblock %}
```

- [ ] **Step 7: 运行测试(应通过)**

```bash
uv run pytest tests/test_tutor_view.py -q
```

Expected: `6 passed`。

- [ ] **Step 8: 手工验证(以导师身份登录)**

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 3
curl -s -c /tmp/tomas.jar -X POST http://localhost:8000/login -d "username=tomas&password=redgum123" -o /dev/null
curl -s -b /tmp/tomas.jar http://localhost:8000/my-sessions | grep -c "Ella Nguyen"
curl -s -o /dev/null -w "%{http_code}\n" -b /tmp/tomas.jar http://localhost:8000/students
kill %1
```

Expected: 第一行至少 `1`(种子里 Tomás 有下周课时);第二行 `403`。

- [ ] **Step 9: 提交**

```bash
git add -A
git commit -m "feat(story-09): tutor view of their own upcoming sessions"
```

---

## Task 10: 交付(`story/10-delivery`)

**Files:**
- Create: `README.md`, `docs/handover.md`, `docs/jira-import.csv`
- Modify: `tests/test_foundation.py`(若需要,补一条静态样式断言)

- [ ] **Step 1: 建分支**

```bash
git checkout -b story/10-delivery story/09-tutor-view
```

- [ ] **Step 2: 写 `README.md`**

```markdown
# Redgum Tutoring — Scheduling and Session Tracking

ISYS3001 Managing Software Development · Case Study 3.

A small web application for an after-school tutoring centre: students, tutors and their
availability, sessions, and the centre's day and week schedule. FastAPI + Jinja2 with a
SQLite database — nothing else to install.

## Prerequisites

- Python 3.10 or newer

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://localhost:8000>. The SQLite database `redgum.db` is created and seeded on
first start (delete the file to reset it).

## Demo accounts

Password for all demo accounts: `redgum123` (illustrative values only).

| Username | Role                        |
|----------|-----------------------------|
| deb      | Administrator               |
| helen    | Administrator (also a tutor)|
| tomas    | Tutor                       |

## Running the tests

```bash
pytest
```

## What the system does

- **Students** — add, find, edit and deactivate students with their year level, school and
  family contact.
- **Tutors** — add, edit and deactivate tutors with the subjects they teach.
- **Availability** — record each tutor's availability windows (day, start, end). A tutor can
  have several windows on several days.
- **Sessions** — book a student with a tutor, move it, cancel it, or mark it attended or
  missed. The centre's operating rule is enforced: **a session must fit entirely inside one
  of that tutor's availability windows for that day**, and the system says why when it does
  not.
- **Schedule** — the centre sees a day or a week at a glance and can filter by tutor; a
  student's past and future sessions are listed on their page.
- **Tutor view** — a tutor sees only their own upcoming sessions.

## Project layout

```
app/
  main.py          FastAPI application (middleware, error pages, routers, startup)
  db.py            engine, session factory, get_db, init_db
  models.py        Student, Tutor, AvailabilityWindow, Session, AppUser
  security.py      password hashing, login dependencies, role guard
  services/        students, tutors, availability, sessions (the availability rule), schedule
  routers/         auth, students, tutors, availability, sessions, views
  templates/       Jinja2 templates
  static/style.css single stylesheet (no CDN)
tests/             pytest suite
docs/              design spec, implementation plan, handover, Jira backlog
```

## Configuration

Environment variables (all optional, sensible defaults for local use):

| Variable              | Default                          | Purpose                       |
|-----------------------|----------------------------------|-------------------------------|
| `REDGUM_SECRET_KEY`   | `dev-secret-change-me`           | Session cookie signing key    |
| `REDGUM_DATABASE_URL` | `sqlite:///./redgum.db`          | SQLAlchemy database URL       |

## More documentation

- Design spec: `docs/superpowers/specs/2026-09-24-redgum-tutoring-design.md`
- Handover document: `docs/handover.md`
- Backlog for Jira import: `docs/jira-import.csv`
```

- [ ] **Step 3: 写 `docs/handover.md`(案例第 9 节六部分)**

```markdown
# Redgum Tutoring — Sprint Handover

## 1. What was delivered against scope

| Capability | Jira story | Notes |
|------------|-----------|-------|
| Login with administrator and tutor roles | RG-02 | Signed session cookie, bcrypt passwords |
| Administrator maintains students | RG-03 | Add, search, edit, deactivate; name, year level and family contact required |
| Administrator maintains tutors | RG-04 | Add, edit, deactivate; subjects recorded; deactivated tutors cannot be booked |
| Administrator maintains availability windows | RG-05 | Day, start and end per window; several windows per tutor |
| Booking a session with the availability rule | RG-06 | 60 or 90 minutes; must fit entirely inside one window for that day, with a clear refusal message |
| Moving, cancelling and marking sessions | RG-07 | Re-checks availability on move; cancelled sessions stay visible; attended and missed recorded |
| Day and week schedule, student history | RG-08 | Filter by tutor; a student's past and future sessions are listed |
| Tutor view of their own sessions | RG-09 | Only the signed-in tutor's upcoming sessions |
| Seed data, README, handover, backlog | RG-10 | Runs from a clean checkout with Python only |

All acceptance criteria are covered by automated tests (`pytest`); the availability rule has
its own unit test file (`tests/test_availability_rule.py`).

## 2. What was not delivered, and why

Everything below was asked for by Helen, Deb or Tomás, or appears in the paper documents, but
is out of scope for this sprint. All items sit in the product backlog (`docs/jira-import.csv`).

| Requested | Source | Why parked |
|-----------|--------|-----------|
| Room allocation and room clash detection | Deb, brief | Explicitly out of scope in the brief |
| Detecting overlapping or double bookings | Brief | Explicitly out of scope in the brief |
| Invoices, fees, prepaid packs and payments | Helen, Deb | Explicitly out of scope |
| Tutor timesheets and payroll | Helen, Tomás | Explicitly out of scope |
| SMS or email reminders | Helen | Explicitly out of scope |
| Parent portal and self-service booking | Helen | Explicitly out of scope |
| Video session links | Brief | Explicitly out of scope |
| Blue card expiry tracking | Helen | Explicitly out of scope |
| Accounting reports / Xero | Helen | Explicitly out of scope |
| January intensive, NAPLAN workshops, pizza night | Helen | Not part of the scheduling problem |
| Term unavailability (e.g. Tomás away week 8) | Availability card | Needs a date-specific absence model; next sprint |
| Tutor weekly session cap (8 sessions) | Availability card | A policy rule, not required by the sprint stories |
| "Students who have not booked in three weeks" report | Helen | Reporting is backlog |
| Printing the week per tutor | Deb | The schedule page can be printed from the browser; a dedicated print view is backlog |

## 3. Setup and run instructions from GitHub

See `README.md`. In short: install Python 3.10+, then

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open <http://localhost:8000>. Tests: `pytest`. No database, Node or Docker install is needed.

## 4. Known issues and limitations

1. Sessions are checked against availability only; overlaps between sessions are not detected
   (deliberate — the brief excludes it). Two students can still be booked with one tutor at the
   same time.
2. Availability is stored per weekday and does not know about term dates or school holidays.
   A tutor who is away for one week cannot be marked away; their window would have to be edited.
3. Session states are final: a cancelled, attended or missed session cannot be moved or
   re-opened.
4. Only 60 and 90 minute sessions are accepted (the brief states these are the only lengths).
5. The sign-in form has no CSRF token (the session cookie is `SameSite=Lax`), no rate limiting
   and no password reset. Suitable for the centre's internal use and this course, not for the
   public internet as-is.
6. There is no audit log of who changed what.
7. SQLite suits the centre's scale and a course demonstration; a multi-user deployment would
   want a server database and concurrent-write handling.
8. Lists are filtered by search and date rather than paginated; fine at 140 students and 11
   tutors.
9. The frontend has no automated tests; behaviour is covered end-to-end by the pytest suite.
10. Booking a session in the past is not blocked — the brief does not ask for it, and the
    schedule doubles as a record of what happened.

## 5. Credentials, configuration and environment

- Demo logins: `deb`, `helen` (administrators), `tomas` (tutor); password `redgum123`
  (illustrative only, never real).
- Configuration lives in environment variables with development defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `REDGUM_SECRET_KEY` | `dev-secret-change-me` | Session cookie signing key — must be set for any real use |
| `REDGUM_DATABASE_URL` | `sqlite:///./redgum.db` | Database location |

- Sample `.env`-style values (illustrative):

```bash
export REDGUM_SECRET_KEY="change-me-to-a-long-random-string"
export REDGUM_DATABASE_URL="sqlite:///./redgum.db"
```

- Sample data: seven students, four tutors (one deactivated), their availability windows, the
  case study's diary week with attended, missed and cancelled sessions, and next week's booked
  sessions generated relative to today.

## 6. Recommended next-sprint backlog

In priority order:

1. **Term unavailability** — mark a tutor away for specific dates (Tomás week 8); without it
   the centre must edit windows and remember to change them back.
2. **Overlap detection** — refuse two sessions for the same tutor or student at the same time.
3. **Room allocation and clash detection** — Deb's quarter-hour room turnaround is currently
   managed by hand.
4. **Printable tutor week** — one page per tutor for the week, replacing Deb's photocopied diary.
5. **Invoices and prepaid packs** — two days a month of Deb's time.
6. **SMS reminders** — the night-before reminder Helen keeps asking for.
7. **Attendance and cancellation policy support** — record whether a cancellation was in time
   and whether it is chargeable (the diary's C vs CL distinction).
8. **Audit trail** — who moved or cancelled a session.
9. **Weekly session cap** — warn when a tutor is booked past their stated maximum.
10. **"Not booked in three weeks" report** — Helen's money-walking-out-the-door list.
```

- [ ] **Step 4: 写 `docs/jira-import.csv`**

```csv
Issue Type,Summary,Epic,Priority,Story Points,Sprint,Description
Story,"Project skeleton, models and seed data",Foundation,Highest,3,Sprint 1,"FastAPI app with SQLite, the five models, base template and stylesheet, and idempotent seed data."
Story,"Log in with administrator and tutor roles",Foundation,Highest,3,Sprint 1,"Signed session cookie login; administrators reach the admin pages, tutors only their own sessions."
Story,"Administrator maintains students",Students,Highest,3,Sprint 1,"Add, search, edit and deactivate students; name, year level and a family contact are required."
Story,"Administrator maintains tutors",Tutors,Highest,3,Sprint 1,"Add, edit and deactivate tutors with the subjects they teach; deactivated tutors cannot be booked."
Story,"Administrator maintains tutor availability windows",Tutors,Highest,3,Sprint 1,"Add, edit and remove windows (day, start, end); a tutor may have several windows on several days."
Story,"Book a session that fits the tutor's availability",Sessions,Highest,5,Sprint 1,"60 or 90 minute sessions; the session must fit entirely inside one availability window for that day, otherwise it is refused with a clear reason."
Story,"Move, cancel and mark sessions",Sessions,High,5,Sprint 1,"Move re-checks availability; cancelled sessions stay visible; attended and missed outcomes recorded; finished sessions cannot change."
Story,"Day and week schedule plus student history",Views,High,3,Sprint 1,"The centre sees a day or week and can filter by tutor; a student's past and future sessions are listed."
Story,"Tutor sees their own upcoming sessions",Views,High,3,Sprint 1,"A tutor lists only the sessions booked for them; an empty list rather than an error."
Story,"README, handover and backlog",Delivery,Highest,3,Sprint 1,"Clean-checkout instructions, handover document and the Jira backlog import."
Story,"Term unavailability for tutors",Backlog,Highest,5,Backlog,"Mark a tutor away for specific dates (e.g. Tomás's week 8 placement)."
Story,"Overlap detection",Backlog,High,5,Backlog,"Refuse two sessions for the same tutor or student at the same time."
Story,"Room allocation and clash detection",Backlog,High,8,Backlog,"Assign rooms and refuse two sessions in one room; includes Deb's quarter-hour turnaround."
Story,"Printable tutor week",Backlog,Medium,3,Backlog,"One printable page per tutor for the week."
Story,"Invoices and prepaid packs",Backlog,High,8,Backlog,"Monthly invoices and prepaid session packs; out of scope in the brief."
Story,"SMS reminders",Backlog,Medium,5,Backlog,"Night-before reminder to the family; out of scope in the brief."
Story,"Cancellation policy support",Backlog,Medium,3,Backlog,"Record in-time vs late cancellations and whether they are chargeable."
Story,"Audit trail",Backlog,Medium,5,Backlog,"Who moved, cancelled or marked a session."
Story,"Weekly session cap warning",Backlog,Low,2,Backlog,"Warn when a tutor is booked beyond their stated maximum."
Story,"Students not booked in three weeks",Backlog,Medium,3,Backlog,"A list of students who have not booked recently."
Story,"Parent portal and self-service booking",Backlog,Low,13,Backlog,"Out of scope in the brief."
Story,"Video session links",Backlog,Low,5,Backlog,"Out of scope in the brief."
Story,"Blue card expiry tracking",Backlog,Low,3,Backlog,"Out of scope in the brief."
Story,"Accounting export",Backlog,Low,3,Backlog,"Out of scope in the brief."
```

- [ ] **Step 5: 全量验证(干净环境)**

```bash
rm -f redgum.db
uv run pytest -q
```

Expected: 全部通过(约 70 个测试)。

```bash
uv run uvicorn app.main:app --port 8000 &
sleep 3
# 登录(管理员)→ 排课(合法)→ 排课(越窗,应被拒绝)→ 课表
curl -s -c /tmp/rg.jar -X POST http://localhost:8000/login -d "username=deb&password=redgum123" -o /dev/null
curl -s -o /dev/null -w "book ok: %{http_code}\n" -b /tmp/rg.jar -X POST http://localhost:8000/sessions/new \
  -d "student_id=1&tutor_id=1&subject=Physics&session_date=2026-08-11&start_time=16:00&length_minutes=60"
curl -s -b /tmp/rg.jar -X POST http://localhost:8000/sessions/new \
  -d "student_id=1&tutor_id=1&subject=Physics&session_date=2026-08-11&start_time=18:30&length_minutes=60" \
  | grep -o "would not fit" | head -1
curl -s -o /dev/null -w "schedule: %{http_code}\n" -b /tmp/rg.jar "http://localhost:8000/schedule?view=week"
# 导师视图
curl -s -c /tmp/tomas.jar -X POST http://localhost:8000/login -d "username=tomas&password=redgum123" -o /dev/null
curl -s -o /dev/null -w "my sessions: %{http_code}\n" -b /tmp/tomas.jar http://localhost:8000/my-sessions
curl -s -o /dev/null -w "students as tutor: %{http_code}\n" -b /tmp/tomas.jar http://localhost:8000/students
kill %1
rm -f redgum.db
```

Expected:
```
book ok: 303
would not fit
schedule: 200
my sessions: 200
students as tutor: 403
```

- [ ] **Step 6: 提交**

```bash
git add -A
git commit -m "docs(story-10): README, handover document and Jira backlog"
```

---

## Self-Review 记录(计划自查)

**1. Spec 覆盖检查**

| Spec 章节 | 对应 Task |
|-----------|----------|
| 第 2 节范围(10 故事) | Task 1–10 一一对应 |
| 第 3 节技术选型 | Task 1(依赖、结构、配置) |
| 第 4 节项目结构 | Task 1 建立;各 Task 填充 |
| 第 5 节数据模型 | Task 1 Step 4 |
| 第 6 节领域规则 | Task 6 `validate_slot` + `tests/test_availability_rule.py`;Task 7 改期复用 |
| 第 7 节路由与页面 | Task 2(auth/views)、3(students)、4(tutors)、5(availability)、6–7(sessions)、8(schedule/学生历史)、9(my-sessions) |
| 第 8 节认证与权限 | Task 2(security.py、303/403 语义);各 Task 的 `require_admin` |
| 第 9 节种子数据 | Task 1 Step 10(完整数据,含日记周与动态下周) |
| 第 10 节测试策略 | Task 1–9 各测试文件 |
| 第 11 节运行与交付 | Task 10 README + Step 5 端到端验证 |
| 第 12 节 Git 流程 | 各 Task Step 1 建分支 + 提交 |
| 第 13 节假设 | 体现在代码(终态不可变、60/90、周二–周六、无时区) |
| 第 14 节已知限制 | Task 10 `docs/handover.md` 第 4 节 |

**2. 占位符扫描:** 无 TBD/TODO;所有代码步骤含完整代码;重复性文件(模板、测试)均给出完整内容。

**3. 类型一致性检查:** `validate_slot(tutor, session_date, start_time, length_minutes)` 在 Task 6 定义、Task 7 复用;`get_or_404(db, model, id, label)` 在 Task 5 定义、Task 6/7/8 使用;`render(request, name, context, status_code)` 全局一致;`bookable_tutors` 在 Task 4 定义、Task 6 使用;`week_start`/`week_days`/`sessions_on` 在 Task 8 内部一致;Jinja 过滤器 `time12`/`date_long` 在 Task 5 注册、Task 5–9 模板使用。



