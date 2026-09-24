import os

SECRET_KEY = os.environ.get("REDGUM_SECRET_KEY", "dev-secret-change-me")
SESSION_MAX_AGE_SECONDS = 60 * 60 * 12
DATABASE_URL = os.environ.get("REDGUM_DATABASE_URL", "sqlite:///./redgum.db")
COOKIE_SECURE = os.environ.get("REDGUM_COOKIE_SECURE", "").lower() in ("1", "true", "yes")
