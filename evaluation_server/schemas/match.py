import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, Json
from schemas.episode import Episode


class MatchResult(BaseModel):
    hash: str = Field(
        ...,
        title="Hash",
        description="A unique hash which acts as an identifier for the said match.",
    )
    ranks: List[str] = Field(
        ...,
        title="Ranks",
        description="A list of the episode specific hash-ids ranked based on the order of preference of the user (Lower index is better).",
    )
    is_draw: bool = Field(
        False,
        title="Is Draw ?",
        description="A boolean flag specifying if this match is a draw - meaning, all the entries are either equally good or equally bad.",
    )
    eval_metadata: Json = Field(
        "{}",
        title="Evaluation response metadata",
        description="JSON object representing all the metadata collected during the evaluation",
    )

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "hash": "e73db6c9-32ae-4803-a07c-df1f3511b759",
                "ranks": [
                    "57a7ae1d-9a47-42f6-9f13-a97e1a6c94bb",
                    "c81f05ba-662b-4e1a-a80c-49695c77744d",
                ],
                "is_draw": False,
            }
        }


class MatchObject(BaseModel):
    hash: str = Field(
        ...,
        title="Hash",
        description="A unique hash which acts as an identifier for the said match.",
    )
    created_at: datetime.datetime = Field(
        ...,
        title="Created At",
        description="Creation datetime of this match",
    )
    updated_at: datetime.datetime = Field(
        ...,
        title="Updated At",
        description="Update datetime of this match",
    )
    expiry_at: datetime.datetime = Field(
        ...,
        title="Expiry At",
        description="Expiry datetime of this match",
    )
    task: str = Field(..., title="Task", description="Task of the Match")
    episodes: List[Episode]
    result: Optional[MatchResult]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "hash": "e73db6c9-32ae-4803-a07c-df1f3511b759",
                "created_at": "2021-05-24T07:37:46.796144",
                "updated_at": "2021-05-24T07:37:46.796155",
                "expiry_at": "2021-05-24T07:47:46.796163",
                "episodes": [
                    {
                        "hash": "57a7ae1d-9a47-42f6-9f13-a97e1a6c94bb",
                        "video_filename": "141a3576-9c8b-4fb1-8fe8-b74613ad6fad.mp4",
                        "video_uri": "/static/uploads/141a3576-9c8b-4fb1-8fe8-b74613ad6fad.mp4",
                        "agent_name": "agent_xyz",
                        "created_at": "2021-05-24T07:37:37.824730",
                    },
                    {
                        "hash": "c81f05ba-662b-4e1a-a80c-49695c77744d",
                        "video_filename": "f8c2aa02-cde7-4ee5-b9a4-e66d66122640.mp4",
                        "video_uri": "/static/uploads/f8c2aa02-cde7-4ee5-b9a4-e66d66122640.mp4",
                        "agent_name": "agent_abc",
                        "created_at": "2021-05-24T07:37:35.686489",
                    },
                ],
            }
        }


class GetMatchByUsernameResponse(BaseModel):
    aicrowd_username: str
    match: MatchObject
