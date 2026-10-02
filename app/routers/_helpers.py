from fastapi import HTTPException
from sqlalchemy.orm import Session as OrmSession


def get_or_404(db: OrmSession, model, object_id: int, label: str):
    obj = db.get(model, object_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{label} not found")
    return obj
