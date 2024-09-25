# models/runner_log_model.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SqlEnum
from sqlalchemy.orm import relationship
from .base import Base
from .runner_model import RunnerStatusEnum  
from datetime import datetime
from enum import Enum

class LogLevelEnum(Enum):
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
    log_level = Column(SqlEnum(LogLevelEnum), default=LogLevelEnum.INFO, nullable=False)
    
    previous_status = Column(SqlEnum(RunnerStatusEnum), nullable=True)
    new_status = Column(SqlEnum(RunnerStatusEnum), nullable=True)

    # Relationship back to RunnerModel
    # runner = relationship('RunnerModel', back_populates='logs')
