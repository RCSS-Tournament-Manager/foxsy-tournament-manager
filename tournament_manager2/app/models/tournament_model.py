from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from .base import Base


class TournamentModel(Base):
    __tablename__ = 'tournaments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    user_id = Column(Integer)
    start_at = Column(String)
    done = Column(Boolean, default=False)

    teams = relationship('TeamModel', back_populates='tournament')
    games = relationship('GameModel', back_populates='tournament')


    def __repr__(self):
        teams = ', '.join([team.name for team in self.teams])
        return (f"<TournamentModel(id={self.id}, name={self.name}, user_id={self.user_id}, start_at={self.start_at}, "
                f"teams=[{teams}])>")