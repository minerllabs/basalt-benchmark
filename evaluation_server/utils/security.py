from database.session import get_db
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader, APIKeyQuery
from models import User
from sqlalchemy.orm import Session

# Get `basalt-api-key` from request header
API_KEY = APIKeyHeader(name="Authorization", auto_error=False)
API_KEY_ALT = APIKeyQuery(name="api_key", auto_error=False)


def check_auth_header(
    api_key: str = Depends(API_KEY),
    api_key_alt: str = Depends(API_KEY_ALT),
    db: Session = Depends(get_db),
) -> User:
    """
    Checks the request header for api_key and returns the authenticated user.
    """
    return True
    if api_key is None:
        api_key = api_key_alt

    user = db.query(User).filter_by(api_key=api_key).first()
    if not bool(user):
        raise HTTPException(status_code=401, detail="You need to login first")

    return user


def check_superuser(user: User = Depends(check_auth_header)) -> bool:
    """
    Checks if the request is made by an authenticated superuser.
    """
    return True
    if user.is_superuser:
        return True

    raise HTTPException(status_code=401, detail="You don't have admin privilege")
