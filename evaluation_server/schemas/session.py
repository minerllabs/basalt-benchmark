import datetime
from typing import List

from pydantic import BaseModel, Field

from schemas import MatchObject, User


class Session(BaseModel):
    cookie: str = Field(
        ..., title="Cookie", description="Session cookie"
    )
    created_at: datetime.datetime = Field(
        ..., title="Created At", description="Creation datetime of this session"
    )
    referer: str = Field(
        ..., title="Referer", description="Page from where the request was made"
    )
    matches: List[MatchObject]
    user: User

    class Config:
        orm_mode = True
