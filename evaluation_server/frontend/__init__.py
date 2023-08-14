from fastapi import APIRouter, Security

from .endpoints import index, leaderboard, agent_performance_image, validate
from utils.security import check_auth_header, check_superuser

frontend_router = APIRouter()

frontend_router.include_router(index.router, tags=["Human evaluation interface page"])
frontend_router.include_router(validate.router, tags=["Validate routes"], dependencies=[Security(check_superuser)])
frontend_router.include_router(leaderboard.router, tags=["Leaderboard page"])
frontend_router.include_router(agent_performance_image.router, tags=["Agent performance image"])
