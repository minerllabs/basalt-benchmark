from typing import List, Tuple

from fastapi import Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import Config
from database.session import get_db
from models import Agent, Episode, Match, MatchResult


async def get_agents_for_match(task: str, db: Session = Depends(get_db)) -> List[Agent]:
    """
    Get agents having at least one episode by querying database
    """
    if task not in Config.BASALT_TASKS:
        raise HTTPException(422, "Invalid task")

    agents = [
        query_output[0]
        for query_output in db.query(Agent, func.count(Episode.id))
        .join(Agent.episodes)
        .group_by(Agent.id)
        .filter_by(task=task)
        .all()
    ]

    return agents


async def get_agent_matches_result(
    agent: Agent, db: Session = Depends(get_db)
) -> List[Tuple[Match, MatchResult, str]]:
    """
    Get all the processed matches of an agent
    """
    query = (
        db.query(Match, MatchResult, Episode.hash)
        .join(Episode.matches)
        .join(MatchResult, Match.id == MatchResult.match_id)
        .filter(
            Episode.agent_id == agent.id,
            Match.is_processed == True,
        )
        .all()
    )

    return query
