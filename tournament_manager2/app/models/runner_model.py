from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base
from .game_model import GameStatus
from .runner_log_model import RunnerLogModel 
from datetime import datetime

class RunnerStatus:
    WAITING = 'waiting'
    RUNNING = 'running'
    COMPLETED = 'completed'

class RunnerModel(Base):
    __tablename__ = 'runners'

    id = Column(Integer, primary_key=True, autoincrement=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'))
    game_id = Column(Integer, ForeignKey('games.id'))
    status = Column(String, default=RunnerStatus.WAITING)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    # Relationships
    tournament = relationship('TournamentModel', back_populates='runners')
    game = relationship('GameModel', back_populates='runner')
    logs = relationship('RunnerLogModel', back_populates='runner', cascade='all, delete-orphan')

    def start_game(self):
        """Start the game by updating the status and start time."""
        self.status = RunnerStatus.RUNNING
        self.start_time = datetime.now()
        self.game.status = GameStatus.IN_PROGRESS

    def finish_game(self, left_score, right_score):
        """Finish the game and record the results."""
        self.status = RunnerStatus.COMPLETED
        self.end_time = datetime.now()
        self.game.status = GameStatus.FINISHED
        self.game.left_score = left_score
        self.game.right_score = right_score

    def log_event(self, message):
        """Add an event to the runner log."""
        log = RunnerLogModel(runner_id=self.id, message=message)
        self.logs.append(log)

    def __repr__(self):
        return (f"<RunnerModel(id={self.id}, tournament_id={self.tournament_id}, "
                f"game_id={self.game_id}, status={self.status})>")
