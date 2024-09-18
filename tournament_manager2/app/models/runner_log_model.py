from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class RunnerLogModel(Base):
    __tablename__ = 'runner_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    runner_id = Column(Integer, ForeignKey('match_runners.id'))
    timestamp = Column(DateTime, default=datetime.now)
    message = Column(String)

    # Relationships
    runner = relationship('MatchRunnerModel', back_populates='logs')

    def __repr__(self):
        return f"<RunnerLogModel(id={self.id}, runner_id={self.runner_id}, timestamp={self.timestamp}, message={self.message})>"
