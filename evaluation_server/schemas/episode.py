import datetime
import os
from typing import Optional

from config import Config
from pydantic import BaseModel, Field, Json, validator
from utils import s3_client


class EpisodeBase(BaseModel):
    agent_name: str = Field(
        ...,
        title="Agent Name",
        description="A unique name to identify the agent that was used in this episode.",
    )

    task: str = Field(
        None,
        title="Task",
        description="One of these tasks: [FindCave, MakeWaterfall, "
        "CreateVillageAnimalPen, BuildVillageHouse]",
    )


class EpisodeCreate(EpisodeBase):
    task: str = Field(
        ...,
        title="Task",
        description="One of these tasks: [FindCave, MakeWaterfall, "
        "CreateVillageAnimalPen, BuildVillageHouse]",
    )


class EpisodeUpdate(EpisodeBase):
    agent_name: str = Field(
        None,
        title="Agent Name",
        description="A unique name to identify the agent that was used in this episode.",
    )


class Episode(EpisodeUpdate):
    hash: str = Field(
        ...,
        title="Hash",
        description="A unique hash which acts as an identifier for the said episode.",
    )
    video_filename: Optional[str] = Field(
        ...,
        title="Filename",
        description="Filename of the rendered video of this episode.",
    )
    video_uri: str = Field(
        "",
        title="Public URI",
        description="A publicly accessible URI for the rendered video of this episode.",
    )

    created_at: datetime.datetime = Field(
        ...,
        title="Created At",
        description="Creation datetime of this episode",
    )

    seed: str = Field(
        ...,
        title="Episode seed",
        description="Seed used to generate this episode video",
    )

    meta: Json = Field(
        "{}",
        title="Episode metadata",
        description="Arbitrary JSON data for this episode video",
    )

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "hash": "5f63fbcb-f136-4fcb-aabd-1b720dd0fb9c",
                "video_filename": "bcd6563c-f04b-4931-acf7-87662d1a50bf.mp4",
                "video_uri": "/static/uploads/bcd6563c-f04b-4931-acf7-87662d1a50bf.mp4",
                "agent_name": "agent_xyz",
                "created_at": "2021-05-24T07:29:44.948027",
                "seed": "seed123",
                "meta": {"key": "value"},
            }
        }
