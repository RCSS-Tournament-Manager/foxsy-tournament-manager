from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class TournamentSatus:
    BEFORE_REGISTRATION = 'before_registration'
    REGISTRATION = 'registration'
    WAIT_TO_START = 'wait_to_start'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'


class TournamentModel(Base):
    __tablename__ = 'tournaments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    user_id = Column(Integer)
    register_open_at = Column(String)
    register_close_at = Column(String)
    start_at = Column(String)
    status = Column(String, default=TournamentSatus.BEFORE_REGISTRATION)

    teams = relationship('TeamModel', back_populates='tournament')
    games = relationship('GameModel', back_populates='tournament')


    def __repr__(self):
        teams = ', '.join([team.name for team in self.teams])
        return (f"<TournamentModel(id={self.id}, name={self.name}, user_id={self.user_id}, start_at={self.start_at}, "
                f"teams=[{teams}], status={self.status})>")