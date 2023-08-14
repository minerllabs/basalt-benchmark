from fastapi import APIRouter, Security

from .endpoints import agent, episode, match, scores, user, session
from utils.security import check_superuser, check_auth_header

api_router = APIRouter()
"""
-Authentication-

    /match - normal user

    All endpoints other than `/match` - superuser
"""
api_router.include_router(agent.router, prefix="/agent", tags=["Agent"], dependencies=[Security(check_superuser)])
api_router.include_router(episode.router, prefix="/episode", tags=["Episode"], dependencies=[Security(check_superuser)])
api_router.include_router(match.router, prefix="/match", tags=["Match"])
api_router.include_router(scores.router, tags=["Scores"], dependencies=[Security(check_superuser)])
api_router.include_router(user.router, prefix="/user", tags=["User"], dependencies=[Security(check_superuser)])
api_router.include_router(session.router, prefix="/session", tags=["Session"], dependencies=[Security(check_superuser)])
