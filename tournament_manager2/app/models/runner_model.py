# models/runner_model.py

from sqlalchemy import Column, Integer, String, DateTime, Enum, UniqueConstraint, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .base import Base
from .game_model import GameModel
from enum import Enum
from datetime import datetime
from utils.messages import *

class RunnerModel(Base):
    __tablename__ = 'runners'

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(SQLEnum(RunnerStatusMessageEnum, native_enum=False), default=RunnerStatusMessageEnum.UNKNOWN, nullable=False)
    address = Column(String, nullable=False, unique=True)
    available_games_count = Column(Integer, default=0, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    requested_command = Column(SQLEnum(RunnerCommandMessageEnum, native_enum=False), default=RunnerCommandMessageEnum.NONE, nullable=False)
    # runner.api_key = "api-key" maybe?  is it safe?
    
    
    # Relationships
    games = relationship('GameModel', back_populates='runner')
    # logs = relationship('RunnerLogModel', back_populates='runner')

    def __repr__(self):
        return ""
        game_ids = [game.id for game in self.games]
        return (f"<RunnerModel(id={self.id}, games={game_ids}, status={self.status.value}, address={self.address})>")
