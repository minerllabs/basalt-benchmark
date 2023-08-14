import datetime
import os

from config import Config
from database import Base
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from utils import s3_client, uuid_gen

from .match import match_registry


class Episode(Base):
    __tablename__ = "episodes"
    id = Column(Integer, primary_key=True, index=True)
    hash = Column(String, default=uuid_gen, index=True)
    video_filename = Column(
        String,
    )
    video_uri_public = Column(
        String, nullable=True
    )  # Used when supplied a video_uri instead of uploading the video
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    seed = Column(String, nullable=False)
    meta = Column(JSON, default="{}")
    task = Column(String)

    agent_id = Column(Integer, ForeignKey("agents.id"))
    agent = relationship("Agent", back_populates="episodes")

    @property
    def agent_name(self):
        return self.agent.name

    matches = relationship("Match", secondary=match_registry, back_populates="episodes")

    def __repr__(self):
        return "<Episode id={} agent_id={} task={} seed={} video_filename='{}'>".format(
            self.id, self.agent_id, self.task, self.seed, self.video_filename
        )

    @property
    def video_uri(self):
        """
        Dynamically generate the video_uri based on the
        filename
        """
        if self.video_uri_public:
            return self.video_uri_public

        if Config.FILES_STORAGE_BACKEND == "local":
            return os.path.join(Config.UPLOADS_BASE_URI, self.video_filename)
        else:
            return s3_client.get_presigned_url(self.video_filename)
