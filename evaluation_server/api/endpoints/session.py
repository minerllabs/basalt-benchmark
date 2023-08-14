from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database.session import get_db

router = APIRouter()


@router.get("/", response_model=List[schemas.Session])
def get_sessions(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    GET request to fetch Match sessions ordered by most recent match results
    """
    return (
        db.query(models.Session)
        .order_by(models.Session.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get("/{session_cookie}", response_model=schemas.Session)
def get_session_by_cookie(session_cookie: str, db: Session = Depends(get_db)):
    db_session = db.query(models.Session).filter_by(cookie=session_cookie).first()
    if not bool(db_session):
        raise HTTPException(404, "Session does not exist")

    return db_session
