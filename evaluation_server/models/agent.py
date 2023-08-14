from database import Base
from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Float


class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)

    base_rating = Column(Integer, default=0)
    reputation_mu = Column(Float, default=25.0)
    reputation_sigma = Column(Float, default=25 / 3)

    task = Column(String)
    is_processed = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=False)

    episodes = relationship("Episode", back_populates="agent", cascade="all,delete")

    __table_args__ = (UniqueConstraint("name", "task"),)

    @property
    def matches(self):
        MATCHES = []
        for _episode in self.episodes:
            MATCHES += _episode.matches
        return MATCHES

    @hybrid_property
    def score(self):
        """
        Returns the conservative score
        """
        return self.reputation_mu - 3 * self.reputation_sigma

    @hybrid_property
    def episode_count(self) -> int:
        """
        Returns number of episodes of the agent
        """
        if self.episodes:
            return len(self.episodes)
        else:
            return 0

    def __repr__(self):
        return "<Agent id={} mu={} sigma={} task={} num_episodes={}>".format(
            self.id,
            self.reputation_mu,
            self.reputation_sigma,
            self.task,
            len(self.episodes),
        )

    def __lt__(self, other):
        return self.id < other.id
