# game_model.py

from sqlalchemy import Column, Integer, String, ForeignKey #, CheckConstraint
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
    runner_id = Column(Integer, ForeignKey('runners.id'), index=True)
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
    runner = relationship('RunnerModel', back_populates='games') 

    # __table_args__ = ( # TODO: ino barye in constraint score > 0 age bekhaym?
    #     CheckConstraint(left_score >= 0, name='check_left_score_nonnegative'),
    #     CheckConstraint(right_score >= 0, name='check_right_score_nonnegative'),
    # )

    def __repr__(self):
        return (f"<GameModel(id={self.id}, left_team={self.left_team.name}, "
                f"right_team={self.right_team.name}, status={self.status}, "
                f"left_score={self.left_score}, right_score={self.right_score}, "
                f"runner_id={self.runner_id})>")
