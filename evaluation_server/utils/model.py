import datetime
import uuid

from config import Config


def uuid_gen():
    """
    Return UUID string
    """
    return str(uuid.uuid4())


def expiry_time():
    """
    Return datetime with increment of `MATCH_EXPIRY_TIME_MINS` setting
    """
    return datetime.datetime.utcnow() + datetime.timedelta(minutes=Config.MATCH_EXPIRY_TIME_MINS)
