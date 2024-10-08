# models/runner_model.py

from sqlalchemy import Column, Integer, String, DateTime, Enum, UniqueConstraint, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .base import Base
from .game_model import GameModel
from enum import Enum
from datetime import datetime
from utils.messages import RunnerStatusMessageEnum

class RunnerStatusEnum(str, Enum):
    RUNNING = 'running'
    PAUSED = 'paused'
    UNKNOWN = 'unknown'
    CRASHED = 'crashed'

    def to_RunnerStatusMessageEnum(self):
        if self == RunnerStatusEnum.RUNNING:
            return RunnerStatusMessageEnum.RUNNING
        elif self == RunnerStatusEnum.PAUSED:
            return RunnerStatusMessageEnum.PAUSED
        elif self == RunnerStatusEnum.UNKNOWN:
            return RunnerStatusMessageEnum.UNKNOWN
        elif self == RunnerStatusEnum.CRASHED:
            return RunnerStatusMessageEnum.CRASHED
        else:
            return RunnerStatusMessageEnum.UNKNOWN

class RunnerModel(Base):
    __tablename__ = 'runners'

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(SQLEnum(RunnerStatusEnum, native_enum=False), default=RunnerStatusEnum.UNKNOWN, nullable=False)
    address = Column(String, nullable=False, unique=True)
    available_games_count = Column(Integer, default=0, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # Relationships
    games = relationship('GameModel', back_populates='runner')
    # logs = relationship('RunnerLogModel', back_populates='runner')

    def __repr__(self):
        return ""
        game_ids = [game.id for game in self.games]
        return (f"<RunnerModel(id={self.id}, games={game_ids}, status={self.status.value}, address={self.address})>")
