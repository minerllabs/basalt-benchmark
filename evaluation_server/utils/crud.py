from fastapi import Depends, encoders
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Base
from database.session import get_db


async def update(db_obj: Base, update_schema_obj: BaseModel, db: Session = Depends(get_db)) -> Base:
    """
    Utility function for `update` endpoint.

    :params db_obj: Database object need to be updated
    :params update_schema_obj: Pydantic model object containing update data
    :params db: Database session

    :returns db_obj: Updated database object
    """
    db_obj_data = encoders.jsonable_encoder(db_obj)
    update_data = update_schema_obj.dict(exclude_unset=True)
    for field in db_obj_data:
        if field in update_data:
            setattr(db_obj, field, update_data[field])

    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
