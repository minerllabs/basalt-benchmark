from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
import datetime

from sqlalchemy.orm import relationship

from database import Base
from utils import uuid_gen


class Session(Base):
    __tablename__ = "sessions"
    id = Column(String, primary_key=True, index=True, default=uuid_gen)
    cookie = Column(String, default=uuid_gen)
    created_at = Column(DateTime, default=datetime.datetime.utcnow())
    referer = Column(String, default=None)
    matches = relationship(
        "Match", back_populates="session"
    )
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"))
    user = relationship(
        "User", back_populates="sessions"
    )
