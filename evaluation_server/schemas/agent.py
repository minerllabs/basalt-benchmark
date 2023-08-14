from typing import List

from pydantic import BaseModel, Field
from schemas.episode import Episode


class AgentBase(BaseModel):
    reputation_mu: float = Field(
        None,
        title="Reputation Mu",
        description="Mu value of the trueskill rating."
    )
    reputation_sigma: float = Field(
        None,
        title="Reputation Sigma",
        description="Sigma value of the trueskill rating.",
    )


class AgentCreate(AgentBase):
    name: str = Field(
        ..., title="Name", description="A unique name referencing the said agent."
    )
    task: str = Field(
        ...,
        title="Task",
        description="One of these tasks: [FindCave, MakeWaterfall, "
                    "CreateVillageAnimalPen, BuildVillageHouse]"
    )


class AgentUpdate(AgentBase):
    pass


class Agent(AgentCreate):
    score: float = Field(
        ...,
        title="Score",
        description="Conservative estimate of score computed by (mu - 3*sigma).",
    )


    episodes: List[Episode]

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "name": "agent_xyz",
                "reputation_mu": 25,
                "reputation_sigma": 8.333333333333334,
                "score": 0,
                "episodes": [
                    {
                        "hash": "5f63fbcb-f136-4fcb-aabd-1b720dd0fb9c",
                        "video_filename": "bcd6563c-f04b-4931-acf7-87662d1a50bf.mp4",
                        "video_uri": "/static/uploads/bcd6563c-f04b-4931-acf7-87662d1a50bf.mp4",
                        "agent_name": "asdsad",
                        "created_at": "2021-05-24T07:29:44.948027",
                    }
                ],
            }
        }
