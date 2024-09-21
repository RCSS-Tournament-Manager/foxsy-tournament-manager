# models/runner_model.py

from sqlalchemy import Column, Integer, String, DateTime, Enum, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from .game_model import GameModel
from .runner_log_model import RunnerLogModel
from enum import Enum
from datetime import datetime

class RunnerStatusEnum(str, Enum):
    RUNNING = 'running'
    INGAME = 'ingame'
    PAUSED = 'paused'
    UNKNOWN = 'unknown'
    CRASHED = 'crashed'

class RunnerModel(Base):
    __tablename__ = 'runners'

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(Enum(RunnerStatusEnum), default=RunnerStatusEnum.UNKNOWN, nullable=False)
    address = Column(String, nullable=False, unique=True)
    available_games_count = Column(Integer, default=0, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # Relationships
    games = relationship('GameModel', back_populates='runner', cascade='save-update, merge') 
    logs = relationship('RunnerLogModel', back_populates='runner', cascade='save-update, merge')

    def __repr__(self):
        game_ids = [game.id for game in self.games]
        return (f"<RunnerModel(id={self.id}, games={game_ids}, status={self.status.value}, address={self.address})>")
