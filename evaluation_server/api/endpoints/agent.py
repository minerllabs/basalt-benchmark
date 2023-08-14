from typing import List

from fastapi import APIRouter, Depends, HTTPException, encoders
from sqlalchemy.orm import Session

import models
import schemas
from config import Config
from database.session import get_db
from utils.crud import update

router = APIRouter()


@router.get("/", response_model=List[schemas.Agent])
async def get_agents(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return db.query(models.Agent).offset(skip).limit(limit).all()


@router.get(
    "/{agent_name}/{task}",
    response_model=schemas.Agent,
    summary="Get details about an agent",
    description="Get details about an agent - including its associated episodes, its current reputation score, etc",
)
async def get_agent(agent_name: str, task: str, db: Session = Depends(get_db)):
    #   Check if agent_name already exists
    agent = db.query(models.Agent).filter_by(
        name=agent_name.strip(), task=task).first()
    if not bool(agent):
        raise HTTPException(status_code=404, detail="Agent Not Found.")

    return agent


@router.post(
    "/",
    response_model=schemas.Agent
)
async def create_agent(agent: schemas.AgentCreate, db: Session = Depends(get_db)):
    if bool(db.query(models.Agent).filter_by(name=agent.name, task=agent.task).first()):
        raise HTTPException(422, "Agent already exists")

    if agent.task not in Config.BASALT_TASKS:
        raise HTTPException(422, "Invalid task")

    db_agent = models.Agent(
        name=agent.name,
        reputation_mu=agent.reputation_mu,
        reputation_sigma=agent.reputation_sigma,
        task=agent.task,
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


@router.patch(
    "/{agent_name}/{task}",
    response_model=schemas.Agent
)
async def update_agent(agent_name: str, task: str, agent: schemas.AgentUpdate, db: Session = Depends(get_db)):
    db_agent = db.query(models.Agent).filter_by(
        name=agent_name, task=task).first()
    if not bool(db_agent):
        raise HTTPException(404, "Agent does not exist")

    return await update(db_obj=db_agent, update_schema_obj=agent, db=db)


@router.delete(
    "/{agent_name}/{task}",
    response_model=schemas.Agent
)
async def delete_agent(agent_name: str, task: str, db: Session = Depends(get_db)):
    agent = db.query(models.Agent).filter_by(
        name=agent_name, task=task).first()
    if not bool(agent):
        raise HTTPException(404, "Agent does not exist")

    # Don't delete if any match is associated with Agent episodes
    episodes = list(agent.episodes)
    for episode in episodes:
        if len(episode.matches) > 0:
            raise HTTPException(
                422, "Match is associated with Agent's episode")

    db.delete(agent)
    db.commit()
    return agent
