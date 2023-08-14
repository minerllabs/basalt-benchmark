from typing import List

import models
import schemas
from database.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/scores.json", response_model=List[schemas.Agent])
async def get_scores_json(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    agents = (
        db.query(models.Agent)
        .order_by(models.Agent.reputation_mu.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return agents
