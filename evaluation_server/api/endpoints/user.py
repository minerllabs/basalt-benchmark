from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from database.session import get_db
from utils.crud import update

router = APIRouter()


@router.post("/", response_model=schemas.User)
async def create_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    user = models.User(
        aicrowd_username=user_in.aicrowd_username,
        is_superuser=user_in.is_superuser,
        is_trusted=user_in.is_trusted,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("/", response_model=List[schemas.User])
async def get_users(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(models.User).offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=schemas.User)
async def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter_by(id=user_id).first()
    if not bool(db_user):
        raise HTTPException(404, "User does not exist")

    return db_user


@router.patch("/{user_id}", response_model=schemas.User)
async def update_user(user_id: str, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = await get_user_by_id(user_id=user_id, db=db)

    return await update(db_obj=db_user, update_schema_obj=user, db=db)


@router.delete("/{user_id}", response_model=schemas.User)
async def delete_user(user_id: str, db: Session = Depends(get_db)):
    db_user = await get_user_by_id(user_id=user_id, db=db)

    # Don't delete if any match is associated with an episodes
    if len(db_user.sessions) > 0:
        raise HTTPException(422, "Session is associated with the user")

    db.delete(db_user)
    db.commit()
    return db_user
