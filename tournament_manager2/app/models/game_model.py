from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class GameStatus:
    PENDING = 'pending'
    IN_QUEUE = 'in_queue'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'


class GameModel(Base):
    __tablename__ = 'games'

    id = Column(Integer, primary_key=True)
    left_team_id = Column(Integer, ForeignKey('teams.id'))
    right_team_id = Column(Integer, ForeignKey('teams.id'))
    tournament_id = Column(Integer, ForeignKey('tournaments.id'))
    status = Column(String, default=GameStatus.PENDING)
    left_score = Column(Integer, default=0)
    right_score = Column(Integer, default=0)

    tournament = relationship('TournamentModel', back_populates='games')
    left_team = relationship('TeamModel', foreign_keys='GameModel.left_team_id')
    right_team = relationship('TeamModel', foreign_keys='GameModel.right_team_id')

    def __repr__(self):
        return (f"<GameModel(id={self.id}, left_team={self.left_team.name}, right_team={self.right_team.name}, "
                f"status={self.status}, left_score={self.left_score}, right_score={self.right_score})>")