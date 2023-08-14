import datetime
import itertools
import json
import math
import random
from itertools import combinations
from queue import PriorityQueue
from typing import List

import models
import schemas
import trueskill
from config import Config
from database.session import get_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session
from utils.check_valid_match_result import check_valid_match_result
from utils.query import get_agents_for_match
from utils.security import check_auth_header, check_superuser
from utils.session_cookies import get_user_session

router = APIRouter()


def win_probability(rating_agent_1, rating_agent_2):
    """
    Pulled from Trueskill website
    This does not seem to account for draw probability as part of the probability mass ,
    which seems okay for our purposes
    """
    ts = trueskill.global_env()
    delta_mu = rating_agent_1.mu - rating_agent_2.mu
    sum_sigma = sum(r.sigma**2 for r in [rating_agent_1, rating_agent_2])
    denom = math.sqrt((ts.beta * ts.beta) + sum_sigma)
    return ts.cdf(delta_mu / denom)


def uncertainty_cost(
    rating_agent_1: trueskill.Rating, rating_agent_2: trueskill.Rating
):
    """
    The utility of a pair of agents with given ratings
    """
    return rating_agent_1.sigma**2 + rating_agent_2.sigma**2


def get_expected_uncertainty_decrease(agent1: models.Agent, agent2: models.Agent):
    """
    Given two agents, calculated the expect delta in utility that would come from their
    playing one another. This is calculated by:
    - Defining a utility function (here simply the summed squared sigmas)
    - Simulated the rankings that would result from the world where each agent won, and what utility that
    pair of rankings would have
    - Taking an expected value of utility by summing those simulations, weighted by the
    likelihood of each agent winning
    """
    ratings = [
        trueskill.Rating(mu=agent1.reputation_mu, sigma=agent1.reputation_sigma),
        trueskill.Rating(mu=agent2.reputation_mu, sigma=agent2.reputation_sigma),
    ]

    win_probas = list()
    # win_probas will contain [p(agent1_win), p(agent2_win)]
    # without accounting for draw probability, so summing to 1
    win_probas.append(win_probability(ratings[0], ratings[1]))
    win_probas.append(1 - win_probas[0])

    # new_ratings is filled with the potential updated rankings in the world where [agent_1_wins, agent_2_wins]
    new_ratings = list()
    # Rating for where 1 beats 2 goes first
    new_ratings.append(trueskill.rate_1vs1(ratings[0], ratings[1]))
    # Then rating for when 2 beats 1
    new_ratings.append(trueskill.rate_1vs1(ratings[1], ratings[0]))

    prior_uncertainty = uncertainty_cost(*ratings)
    win_uncertainty = uncertainty_cost(*new_ratings[0])
    loss_uncertainty = uncertainty_cost(*new_ratings[1])

    # Calculated expected decrease in uncertainty, weighted by that scenario's probability
    expected_uncertainty_decrease = win_probas[0] * (
        prior_uncertainty - win_uncertainty
    ) + win_probas[1] * (prior_uncertainty - loss_uncertainty)
    return expected_uncertainty_decrease


def add_new_matches(task: str, db: Session, top_k: int = 25):
    """
    This is typically run as a background task, unless somehow number of available matches hits 0.
    It works by:
    - Creating all N-choose-2 combinations of current agents
    - For each pair, calculate the expected utility gain that would come from a match between those agents
    - Add the top `top_k` matches to the database, with a randomly selected episode used for each

    """
    agents = db.query(models.Agent).filter_by(task=task, is_approved=True).all()
    if len(agents) < 2:
        raise HTTPException(
            status_code=404, detail="Not enough agents to generate a match."
        )
    pq = PriorityQueue(maxsize=top_k)

    for agent1, agent2 in combinations(agents, 2):
        expected_uncertainty_decrease = get_expected_uncertainty_decrease(
            agent1, agent2
        )
        queue_entry = (expected_uncertainty_decrease, (agent1, agent2))
        if not pq.full():
            pq.put(queue_entry)
        else:
            _ = pq.get()
            pq.put(queue_entry)

    existing_matches = (
        db.query(models.Match)
        .filter_by(is_selected=False)
        .filter_by(is_processed=False)
    )
    while not pq.empty():
        priority, player_pair = pq.get()
        episode_seed_group = dict()
        for episode in itertools.chain(
            player_pair[0].episodes, player_pair[1].episodes
        ):
            episode_seed_group.setdefault(episode.seed, list()).append(episode)
        episodes_list = [
            episode_list
            for episode_list in episode_seed_group.values()
            if len(episode_list) == 2
        ]
        if len(episodes_list) == 0:
            raise HTTPException(404, detail="No episodes with same seed exist.")
        match = models.Match(task=task)
        match.episodes = random.choice(episodes_list)
        match.priority_value = priority
        db.add(match)
    existing_matches.delete()
    db.commit()


########################################################################
########################################################################
# - MATCH
#
########################################################################
########################################################################


@router.get(
    "/",
    response_model=schemas.MatchObject,
    summary="Get a binary comparison to decide on",
    description="Get a match of two episodes from two separate agents",
)
async def get_match(
    task: str,
    background_tasks: BackgroundTasks,
    user: models.User = Depends(check_auth_header),
    db: Session = Depends(get_db),
):
    """
    Look for existing available matches (of which there should be some, unless we just started the server), and
    return the match with the highest priority value

    If we would end up with a match buffer below our refill threshold, or if we haven't refreshed
    matches recently, run a background task of adding new matches to the database

    """

    if task not in Config.BASALT_TASKS:
        raise HTTPException(422, "Invalid task")

    available_matches = (
        db.query(models.Match)
        .filter_by(is_selected=False, task=task, is_processed=False)
        .order_by(models.Match.priority_value.desc())
    )

    if available_matches.count() == 0:
        add_new_matches(task, db)
        available_matches = (
            db.query(models.Match)
            .filter_by(is_selected=False, task=task, is_processed=False)
            .order_by(models.Match.priority_value.desc())
        )

    chosen_match = available_matches[0]
    # TODO figure out how we want to do expiration more cleanly
    if (
        available_matches.count() < Config.BUFFER_REFILL_THRESHOLD
        or chosen_match.created_at
        < (datetime.datetime.utcnow() - datetime.timedelta(minutes=5))
    ):
        background_tasks.add_task(
            add_new_matches, task=task, db=db, top_k=Config.MATCH_BUFFER_SIZE
        )

    chosen_match.is_selected = True
    db.add(chosen_match)
    db.commit()

    return chosen_match


@router.post(
    "/",
    response_model=schemas.MatchObject,
    summary="Update a match with human evaluation results",
    description="Update a match with the human evaluation results",
)
async def update_match(
    result: schemas.MatchResult,
    background_tasks: BackgroundTasks,
    session: models.Session = Depends(get_user_session),
    db: Session = Depends(get_db),
):
    hash = result.hash
    ranks = result.ranks
    is_draw = result.is_draw

    ################################################################################
    # Validation
    #
    #   - The match hash should be a valid hash
    #   - The match should not be expired
    #   - The match should not already be processed
    ################################################################################

    # Obtain match object
    match = db.query(models.Match).filter_by(hash=hash).first()
    await check_valid_match_result(match)

    # Obtain episode objects (the loop is in place for future generalizability)
    episodes = []
    agents = []
    ratings = []
    for _hash in ranks:
        _episode = db.query(models.Episode).filter_by(hash=_hash).first()
        if not bool(_episode):
            raise HTTPException(
                status_code=401, detail="Unknown episode hash provided."
            )
        if _episode not in match.episodes:
            raise HTTPException(
                status_code=401,
                detail="Provided episode hashes do not match the expected episode hashes for this match.",
            )

        episodes.append(_episode)
        _agent = _episode.agent
        agents.append(_agent)
        ratings.append(
            (trueskill.Rating(mu=_agent.reputation_mu, sigma=_agent.reputation_sigma),)
        )

    ################################################################################
    # Compute Score Updates
    #
    #   - ratings : List containing the trueskill Rating object
    ################################################################################
    ranks = list(range(len(ratings)))  # [0, 1]
    # In case a draw, we change the rating to - [0, 0]
    if is_draw:
        ranks = [0] * len(ratings)

    updated_ratings = trueskill.rate(ratings, ranks=ranks)

    # Assign updated ratings to agents
    for _idx, agent in enumerate(agents):
        rating = updated_ratings[_idx][0]  # All games will be single player games
        agent.reputation_mu = rating.mu
        agent.reputation_sigma = rating.sigma
        # Schedule for DB update
        db.add(agent)

    match.is_processed = True
    match.session = session
    match.updated_at = datetime.datetime.utcnow()
    db.add(match)

    # Add match result
    match_result = models.MatchResult(
        hash=match.hash,
        match=match,
        is_draw=result.is_draw,
        eval_metadata=json.dumps(result.eval_metadata),
    )
    match_result.ranks = result.ranks
    db.add(match_result)

    # Save to DB
    db.commit()

    task = agents[0].task
    new_match_object = await get_match(
        task=task, background_tasks=background_tasks, db=db
    )
    # Return a new match_object
    return new_match_object


def find_episode_by_seed(episodes, seed):
    for episode in episodes:
        if episode.seed == seed:
            return episode
    return None

@router.post(
    "/add-match",
    response_model=schemas.MatchObject,
    summary="Add new match entry in the database manually",
)
async def add_match(
    agent1: str,
    agent2: str,
    task: str,
    seed: str,
    db: Session = Depends(get_db),
    is_superuser: bool = Depends(check_superuser),
):
    if not is_superuser:
        raise HTTPException(401, "Unauthorized")

    # Find the agents by name
    agent1 = db.query(models.Agent).filter_by(name=agent1, task=task).first()
    agent2 = db.query(models.Agent).filter_by(name=agent2, task=task).first()

    if not agent1 or not agent2:
        raise HTTPException(401, "Agent not found")

    # Find the episodes by seed
    episode1 = find_episode_by_seed(agent1.episodes, seed)
    episode2 = find_episode_by_seed(agent2.episodes, seed)

    if not episode1 or not episode2:
        raise HTTPException(401, "Episode not found")

    # Create a new match
    match = models.Match(task=task)
    match.episodes = [episode1, episode2]
    db.add(match)
    db.commit()

    return match



@router.get(
    "/list",
    response_model=List[schemas.MatchObject],
    summary="Get a list of most recently updated matches",
)
async def get_matches(
    skip: int = 0,
    limit: int = 20,
    is_superuser: bool = Depends(check_superuser),
    db: Session = Depends(get_db),
):
    if not is_superuser:
        HTTPException(401, "Unauthorized")
    return (
        db.query(models.Match)
        .order_by(models.Match.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/list-by-username",
    response_model=List[schemas.GetMatchByUsernameResponse],
)
async def list_by_username(
    username: str,
    is_superuser: bool = Depends(check_superuser),
    db: Session = Depends(get_db),
):
    if not is_superuser:
        HTTPException(401, "Unauthorized")
    results = (
        db.query(models.Match, models.User.aicrowd_username)
        .join(models.Session, models.Session.id == models.Match.session_id)
        .join(models.User, models.User.id == models.Session.user_id)
        .filter(models.User.aicrowd_username.like(f"%{username}%"))
        .all()
    )
    return [{"match": result[0], "aicrowd_username": result[1]} for result in results]
