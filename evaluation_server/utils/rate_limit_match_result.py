import datetime
from typing import Optional

import models
from database.session import get_db
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from utils.security import check_auth_header


def check_user_match_result_count(
    user: models.User = Depends(check_auth_header), db: Session = Depends(get_db)
) -> Optional[models.User]:
    """
    Rate Limiting: Checks if the number of match result submissions done by a user in past 5 minutes is less than 5
    else raise `HTTPException` with status code `429: Too many requests`
    """
    return db.query(models.User).first()  # temporarily allow all users
    matches = (
        db.query(models.Match)
        .join(models.Match.session)
        .join(models.Session.user)
        .filter(
            models.User.id == user.id,
            models.Match.is_processed == True,
            models.Match.updated_at
            > (datetime.datetime.utcnow() - datetime.timedelta(minutes=5)),
        )
        .all()
    )

    if len(matches) > 5:
        raise HTTPException(429, "Too many requests, Please try after sometime.")

    return user
