import json
import os
import traceback
import uuid
from typing import List, Optional, Union
from urllib.parse import urlparse

import models
import schemas
from config import Config
from database.session import get_db
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, encoders
from pydantic import Json
from sqlalchemy.orm import Session
from utils import upload_file
from utils.crud import update

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.Episode,
    summary="Add an episode video",
    description="Upload a rendered video for an episode",
)
async def episode(
    agent_name: str = Body(...),
    task: str = Body(...),
    seed: str = Body(...),
    meta: Json = Body("{}"),
    file: Optional[UploadFile] = File(None),
    file_uri: Optional[str] = None,
    db: Session = Depends(get_db),
):
    # Check task
    if task not in Config.BASALT_TASKS:
        raise HTTPException(422, "Invalid task")

    # Check if seed is alphanumeric or not
    if not seed.isalnum():
        raise HTTPException(422, "Seed must be alphanumeric")

    # Check if seed is unique
    if (
        db.query(models.Episode)
        .join(models.Agent)
        .filter(
            models.Agent.name == agent_name,
            models.Episode.seed == seed,
            models.Agent.task == task,
        )
        .count()
        > 0
    ):
        raise HTTPException(422, "Seed already exists for agent")
    ####################################################################
    # Handle File Upload
    ####################################################################

    if file is not None:
        file_content = file.file.read()
        try:
            target_filename = upload_file(file_content)
            video_uri_public = None
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(422, "Upload failed")
    else:
        # Here we expect the file_uri to exist
        assert (
            file_uri is not None
        ), "Both file field and file_uri field are not provided, which is not allowed."
        target_filename = os.path.basename(urlparse(file_uri).path)
        video_uri_public = file_uri

    ####################################################################
    # Handle Database Record Keeping
    ####################################################################

    #   - Check if agent_name already exists
    agent = db.query(models.Agent).filter_by(name=agent_name.strip(), task=task).first()
    if not bool(agent):
        #   - If agent by this name does not exist
        #   - Create an agent object with this name
        agent = models.Agent(name=agent_name.strip(), task=task)
        db.add(agent)

    if task != agent.task:
        raise HTTPException(422, "Task mismatch for Agent and Episode")

    # Create a new episode
    episode = models.Episode(
        video_filename=target_filename,
        video_uri_public=video_uri_public,
        seed=seed,
        meta=json.dumps(meta),
        task=task,
    )
    episode.agent = agent
    db.add(episode)
    db.commit()

    return episode


@router.get("/", response_model=List[schemas.Episode])
async def get_episodes(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    return (
        db.query(models.Episode)
        .order_by(models.Episode.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/{episode_hash}",
    response_model=schemas.Episode,
)
async def get_episode(episode_hash: str, db: Session = Depends(get_db)):
    db_episode = db.query(models.Episode).filter_by(hash=episode_hash).first()
    if not bool(db_episode):
        raise HTTPException(404, "Episode does not exist")

    return db_episode


@router.patch(
    "/{episode_hash}",
    response_model=schemas.Episode,
)
async def update_episode(
    episode_hash: str, episode: schemas.EpisodeUpdate, db: Session = Depends(get_db)
):
    db_episode = db.query(models.Episode).filter_by(hash=episode_hash).first()
    if not bool(db_episode):
        raise HTTPException(404, "Episode does not exist")

    # Update agent for this episode
    if bool(episode.agent_name):
        agent = db.query(models.Agent).filter_by(name=episode.agent_name).first()
        if not bool(agent):
            raise HTTPException(404, "Agent does not exist")
        if (
            db.query(models.Episode)
            .join(models.Agent)
            .filter(
                models.Agent.name == episode.agent_name,
                models.Episode.seed == db_episode.seed,
            )
            .count()
            > 0
        ):
            raise HTTPException(422, "Seed already exists for agent")
        if bool(episode.task):
            if episode.task != agent.task:
                raise HTTPException(422, "Task mismatch for Agent and Episode")
        else:
            episode.task = agent.task
        db_episode.agent = agent
    else:
        if bool(episode.task):
            raise HTTPException(422, "Agent name is mandatory with task")

    return await update(db_obj=db_episode, update_schema_obj=episode, db=db)


@router.delete(
    "/{episode_hash}",
    response_model=schemas.Episode,
)
async def delete_episode(episode_hash: str, db: Session = Depends(get_db)):
    db_episode = db.query(models.Episode).filter_by(hash=episode_hash).first()
    if not bool(db_episode):
        raise HTTPException(404, "Episode does not exist")

    # Don't delete if any match is associated with an episodes
    if len(episode.matches) > 0:
        raise HTTPException(422, "Match is associated with the episode")

    # load parent instance to prevent DetachedInstanceError
    agent = db_episode.agent

    db.delete(db_episode)
    db.commit()
    return db_episode
