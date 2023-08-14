from sqlalchemy import Column, String, Boolean
import secrets

from sqlalchemy.orm import relationship

from database import Base
from utils import uuid_gen


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True, default=uuid_gen)
    api_key = Column(String, unique=True, index=True, default=secrets.token_hex)
    aicrowd_username = Column(String, nullable=True)
    is_superuser = Column(Boolean, default=False)
    is_trusted = Column(Boolean, default=True)

    sessions = relationship(
        "Session", back_populates="user", cascade="all,delete"
    )

