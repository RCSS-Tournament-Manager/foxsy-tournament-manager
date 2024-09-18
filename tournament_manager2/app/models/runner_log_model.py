# runner_log_model.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from datetime import datetime

class RunnerLogModel(Base):
    __tablename__ = 'runner_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    runner_id = Column(Integer, ForeignKey('runners.id'), nullable=False, index=True)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    runner = relationship('RunnerModel', back_populates='logs')

    def __repr__(self):
        return (f"<RunnerLogModel(id={self.id}, runner_id={self.runner_id}, "
                f"message='{self.message}', timestamp={self.timestamp})>")
