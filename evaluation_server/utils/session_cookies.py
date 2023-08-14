from fastapi import Request, Response, Depends
from sqlalchemy.orm import Session

from config import Config
from database.session import get_db
import models
from utils.rate_limit_match_result import check_user_match_result_count


def get_user_session(
    request: Request,
    response: Response,
    user: models.User = Depends(check_user_match_result_count),
    db: Session = Depends(get_db),
) -> models.Session:
    """
    Returns the session currently associated with the user by extracting `_basalt_match_session` cookie from request.
    If no cookie exists, then create a new session for the user and set the `_basalt_match_session` cookie in the
    response with expiry time of `SESSION_EXPIRY_TIME_MINS` from config.

    """
    session_cookie = request.cookies.get("_basalt_match_session", None)
    if session_cookie:
        session = db.query(models.Session).filter_by(cookie=session_cookie).first()
    else:
        session = models.Session(
            referer=request.headers.get("Referer", None), user=user
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        response.set_cookie(
            key="_basalt_match_session",
            value=session.cookie,
            expires=Config.SESSION_EXPIRY_TIME_MINS * 60,
        )

    return session
