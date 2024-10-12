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
    STOPPED = 'stopped'
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
        elif self == RunnerStatusEnum.STOPPED:
            return RunnerStatusMessageEnum.STOPPED
        else:
            return RunnerStatusMessageEnum.UNKNOWN

class RunnerCommandEnum(str, Enum):
    # START = 'start'
    STOP = 'stop'
    PAUSE = 'pause'
    RESUME = 'resume'
    # RESTART = 'restart'
    # UNKNOWN = 'unknown'

    def to_RunnerCommandEnum(self):
        # if self == RunnerCommandEnum.START:
        #     return RunnerCommandEnum.START
        if self == RunnerCommandEnum.STOP:
            return RunnerCommandEnum.STOP
        elif self == RunnerCommandEnum.PAUSE:
            return RunnerCommandEnum.PAUSE
        elif self == RunnerCommandEnum.RESUME:
            return RunnerCommandEnum.RESUME
        # elif self == RunnerCommandEnum.RESTART:
        #     return RunnerCommandEnum.RESTART
        # else:
        #     return RunnerCommandEnum.UNKNOWN

class RunnerModel(Base):
    __tablename__ = 'runners'

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(SQLEnum(RunnerStatusEnum, native_enum=False), default=RunnerStatusEnum.UNKNOWN, nullable=False)
    address = Column(String, nullable=False, unique=True)
    available_games_count = Column(Integer, default=0, nullable=False)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=True)
    # runner.api_key = "api-key" maybe?  is it safe?
    
    
    # Relationships
    games = relationship('GameModel', back_populates='runner')
    # logs = relationship('RunnerLogModel', back_populates='runner')

    def __repr__(self):
        return ""
        game_ids = [game.id for game in self.games]
        return (f"<RunnerModel(id={self.id}, games={game_ids}, status={self.status.value}, address={self.address})>")
