# models/runner_log_model.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from .runner_model import RunnerModel, RunnerStatusEnum  
from datetime import datetime
from enum import Enum

class LogLevelEnum(str, Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

class RunnerLogModel(Base):
    __tablename__ = 'runner_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    runner_id = Column(Integer, ForeignKey('runners.id', ondelete='CASCADE'), nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    log_level = Column(Enum(LogLevelEnum), default=LogLevelEnum.INFO, nullable=False)
    
    previous_status = Column(Enum(RunnerStatusEnum), nullable=True)
    new_status = Column(Enum(RunnerStatusEnum), nullable=True)

    # Relationship back to RunnerModel
    runner = relationship('RunnerModel', back_populates='logs')
