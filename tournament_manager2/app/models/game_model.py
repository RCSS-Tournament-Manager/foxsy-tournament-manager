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

    # Relationships
    tournament = relationship('TournamentModel', back_populates='games')
    left_team = relationship(
        'TeamModel',
        foreign_keys=[left_team_id],
        back_populates='left_games'
    )
    right_team = relationship(
        'TeamModel',
        foreign_keys=[right_team_id],
        back_populates='right_games'
    )

    def __repr__(self):
        return (f"<GameModel(id={self.id}, left_team={self.left_team.name}, "
                f"right_team={self.right_team.name}, status={self.status}, "
                f"left_score={self.left_score}, right_score={self.right_score})>")
