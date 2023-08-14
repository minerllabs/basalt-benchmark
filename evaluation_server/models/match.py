import datetime
import json

from database import Base
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
)
from sqlalchemy.orm import relation, relationship
from utils import expiry_time, uuid_gen

match_registry = Table(
    "match_registry",
    Base.metadata,
    Column("match_id", Integer, ForeignKey("matches.id", ondelete="CASCADE")),
    Column("episode_id", Integer, ForeignKey("episodes.id", ondelete="CASCADE")),
)


class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String, default=uuid_gen, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    expiry_at = Column(DateTime, default=expiry_time)
    priority_value = Column(Integer, default=0)
    is_selected = Column(Boolean, default=False)
    is_processed = Column(Boolean, default=False)
    task = Column(String)

    episodes = relationship(
        "Episode",
        secondary=match_registry,
        back_populates="matches",
        cascade="all, delete",
    )

    result = relationship("MatchResult", uselist=False, back_populates="match")

    session_id = Column(String, ForeignKey("sessions.id"))
    session = relationship("Session", back_populates="matches")

    def __repr__(self):
        return "<Match id={} hash={} processed? {} episodes: {} >".format(
            self.id, self.hash, self.is_processed, [x.id for x in self.episodes]
        )


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    hash = Column(String, default=None)
    is_draw = Column(Boolean, default=False)

    _ranks = Column(String, default=None)
    eval_metadata = Column(JSON, default="{}")

    match_id = Column(Integer, ForeignKey("matches.id"))
    match = relation("Match", back_populates="result")

    @property
    def ranks(self):
        return json.loads(self._ranks)

    @ranks.setter
    def ranks(self, ranks):
        self._ranks = json.dumps(ranks)

    def __repr__(self):
        return "<MatchResult id={} rank={} >".format(self.id, self._ranks)
