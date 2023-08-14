import datetime

from fastapi import HTTPException

from models import Match
from config import Config

async def check_valid_match_result(match: Match) -> None:
    """
    Check if the submitted Match result is valid or not
    """

    # Check if Match exists
    match_does_not_exist = not bool(match)
    if match_does_not_exist:
        raise HTTPException(status_code=404, detail="Unknown or expired Match hash")

    # Check if Match is expired
    is_match_expired = (
        datetime.datetime.utcnow() - match.expiry_at
    ).total_seconds() > 0
    if is_match_expired:
        raise HTTPException(status_code=404, detail="Unknown or expired Match hash")

    # Check if match is already processed
    if match.is_processed:
        raise HTTPException(status_code=401, detail="Match has already been processed.")

    # Check if Match result is submitted too early
    if Config.ANTIBOT_ENABLED:
        is_match_result_early = (
            datetime.datetime.utcnow() - match.created_at
        ).total_seconds() < 30
        if is_match_result_early:
            raise HTTPException(status_code=403, detail="Match result submitted too early")
