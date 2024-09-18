# runner_model.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from .base import Base
from .game_model import GameModel, GameStatus
from .runner_log_model import RunnerLogModel 
from datetime import datetime
from enum import Enum

class RunnerStatus: # should we this?
    WAITING = 'waiting'
    RUNNING = 'running'
    READY = 'ready'

# class RunnerStatusEnum(Enum): # or should we this?
#     WAITING = 'waiting'
#     RUNNING = 'running'
#     READY = 'ready'

class RunnerModel(Base):
    __tablename__ = 'runners'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False) 
    status = Column(String, default=RunnerStatus.WAITING) 
    # status = Column(Enum(RunnerStatusEnum), default=RunnerStatusEnum.WAITING, nullable=False)

    ip = Column(String, nullable=True) # maybe?
    port = Column(Integer, nullable=True) # maybe too?
    available_games_count = Column(Integer, default=0, nullable=False)

    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    # Relationships
    games = relationship('GameModel', back_populates='runner', cascade='all, delete-orphan') 
    logs = relationship('RunnerLogModel', back_populates='runner', cascade='all, delete-orphan')

    def start_game(self, game: GameModel):
        """Start a specific game by updating the status and start time."""
        self.status = RunnerStatus.RUNNING
        self.start_time = datetime.utcnow()
        game.status = GameStatus.IN_PROGRESS
        self.log_event(f"Game {game.id} started.")

    def finish_game(self, game: GameModel, left_score: int, right_score: int):
        """Finish a specific game and record the results."""
        self.status = RunnerStatus.READY
        self.end_time = datetime.utcnow()
        game.status = GameStatus.FINISHED
        game.left_score = left_score
        game.right_score = right_score
        self.log_event(f"Game {game.id} finished with scores {left_score}-{right_score}.")

    def log_event(self, message: str):
        """Add an event to the runner log."""
        log = RunnerLogModel(runner_id=self.id, message=message)
        self.logs.append(log)

    def __repr__(self):
        game_ids = [game.id for game in self.games]
        return (f"<RunnerModel(id={self.id}, games={game_ids}, status={self.status.value})>")
