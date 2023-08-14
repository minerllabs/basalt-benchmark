import hashlib
import random
import secrets
from typing import Optional

import models
from config import Config
from database.session import get_db
from fastapi import APIRouter, Depends, HTTPException, Request
from frontend.template import templates
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/")
async def index(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(
        "home.html",
        context={
            "request": request,
            "domain": Config.DOMAIN_NAME,
            "tasks": Config.BASALT_TASKS,
            "eval_questions_required": Config.EVAL_QUESTIONS_REQUIRED,
        },
    )


@router.get("/demo-evaluation")
@router.get("/embed")
async def embed(
    request: Request,
    task: str = "None",
    aicrowd_username: str = "",
    unique_hash: str = "",
    db: Session = Depends(get_db),
):
    # TODO: Re-enable this after MTurk integration is merged

    # expected_hash = hashlib.md5(
    #     (aicrowd_username + Config.UNIQUE_SALT).encode("utf-8")
    # ).hexdigest()
    # if unique_hash != expected_hash:
    #     raise HTTPException(status_code=403, detail="Embed key expired.")

    if task == "None":
        # Anssi: Limit this to something else to fix to specific tasks
        # e.g., task = random.choice(["CreateVillageAnimalPen", "BuildVillageHouse"])
        task = random.choice(Config.BASALT_TASKS)

    user = db.query(models.User).filter_by(aicrowd_username=aicrowd_username).first()
    # TODO: Disabled user auto creation for BASALT 2022, re-enable in case normal users can compare videos like 2021.
    if not bool(user):
        user = models.User(
            aicrowd_username=aicrowd_username, api_key=secrets.token_hex(24)
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    return templates.TemplateResponse(
        "embed.html",
        context={
            "request": request,
            "domain": Config.DOMAIN_NAME,
            "tasks": Config.BASALT_TASKS,
            "current_task": task,
            "current_user": user,
            "eval_questions_required": Config.EVAL_QUESTIONS_REQUIRED,
        },
    )


# @router.get("/old_embed")
# async def embed(
#     task: str,
#     request: Request,
#     aicrowd_username: str = "",
#     unique_hash: str = "",
#     db: Session = Depends(get_db),
# ):
#     # TODO: Re-enable this after MTurk integration is merged

#     # expected_hash = hashlib.md5(
#     #     (aicrowd_username + Config.UNIQUE_SALT).encode("utf-8")
#     # ).hexdigest()
#     # if unique_hash != expected_hash:
#     #     raise HTTPException(status_code=403, detail="Embed key expired.")

#     user = db.query(models.User).filter_by(aicrowd_username=aicrowd_username).first()
#     # TODO: Disabled user auto creation for BASALT 2022, re-enable in case normal users can compare videos like 2021.
#     if not bool(user):
#         user = models.User(
#             aicrowd_username=aicrowd_username, api_key=secrets.token_hex(24)
#         )
#         db.add(user)
#         db.commit()
#         db.refresh(user)

#     return templates.TemplateResponse(
#         "embed-old.html",
#         context={
#             "request": request,
#             "domain": Config.DOMAIN_NAME,
#             "tasks": Config.BASALT_TASKS,
#             "current_task": task,
#             "current_user": user,
#             "eval_questions_required": Config.EVAL_QUESTIONS_REQUIRED,
#         },
#     )
