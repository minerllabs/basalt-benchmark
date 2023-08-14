from typing import List

import models
from database.session import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse
from utils.generate_agent_performance_image import (
    get_results_from_query,
    make_dataframe_from_counts,
    plot_single_swarm,
)
from utils.query import get_agent_matches_result

router = APIRouter()


@router.get("/agents/win-lose.png")
async def get_agent_performance_image(agent_name: str, db: Session = Depends(get_db)):
    agent = db.query(models.Agent).filter_by(name=agent_name).first()
    if not bool(agent):
        raise HTTPException(status_code=404, detail="Agent Not Found.")

    query = await get_agent_matches_result(agent, db)
    result = get_results_from_query(query)
    data = make_dataframe_from_counts(result["counts"])
    image_buffer = plot_single_swarm(data, agent_name=agent_name, order=result["order"])

    return StreamingResponse(image_buffer, media_type="image/png")
