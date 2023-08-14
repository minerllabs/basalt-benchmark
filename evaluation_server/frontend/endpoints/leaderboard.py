from typing import List

import schemas
from config import Config
from database.session import get_db
from fastapi import APIRouter, Depends, Request
from frontend.template import templates
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/scores", response_model=List[schemas.Agent])
async def get_scores(
    request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    return templates.TemplateResponse(
        "leaderboard.html",
        context={
            "request": request,
            "domain": Config.DOMAIN_NAME,
            "skip": skip,
            "limit": limit,
        },
    )
