from datetime import datetime
import hashlib
import humanize
import models
import secrets
from typing import Any, Optional, Union

from fastapi import APIRouter, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from config import Config
from utils.security import check_auth_header
from database.session import get_db
from frontend.template import templates
from fastapi import Form
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/validate")
async def validate(request: Request, expand: Optional[bool] = False, db: Session = Depends(get_db), user: models.User = Depends(check_auth_header)):
    agents = db.query(models.Agent).filter_by(is_processed=False).all()
    agent = None
    timeago = None
    if len(agents) > 0:
        agent = agents[0]
        timeago = humanize.naturaltime(
            datetime.now() - agent.episodes[0].created_at)
    return templates.TemplateResponse("validate.html", context={
        'request': request,
        'agents': agents,
        'agent': agent,
        'timeago': timeago,
        'current_user': user,
        'expand': bool(expand),
    })


@router.get("/validate/{agent}/{task}")
async def validate_process(agent: str, task: str, request: Request, expand: Optional[bool] = False, db: Session = Depends(get_db), user: models.User = Depends(check_auth_header)):
    agents = db.query(models.Agent).filter_by(is_processed=False).all()
    agent = db.query(models.Agent).filter_by(name=agent, task=task).first()
    timeago = humanize.naturaltime(
        datetime.now() - agent.episodes[0].created_at)
    return templates.TemplateResponse("validate.html", context={
        'request': request,
        'agents': agents,
        'agent': agent,
        'timeago': timeago,
        'current_user': user,
        'expand': bool(expand),
    })


@router.post("/validate/{agent_id}/approve")
async def validate_approve(agent_id: str, request: Request, base_rating: int = Form(default=-1), db: Session = Depends(get_db)):
    agent = db.query(models.Agent).filter_by(id=agent_id).first()
    if not agent.is_processed:
        agent.is_processed = True
        agent.is_approved = True
        agent.base_rating = base_rating
        db.add(agent)
        db.commit()
        params = str(request.query_params)
        return RedirectResponse('/validate?' + params, status_code=302)
    return 'Already processed or not found'


@router.post("/validate/{agent}/decline")
async def validate_decline(agent: str, request: Request, db: Session = Depends(get_db)):
    agent = db.query(models.Agent).filter_by(name=agent).first()
    if not agent.is_processed:
        agent.is_processed = True
        agent.is_approved = False
        db.add(agent)
        db.commit()
        params = str(request.query_params)
        return RedirectResponse('/validate?' + params, status_code=302)
    return 'Already processed or not found'
