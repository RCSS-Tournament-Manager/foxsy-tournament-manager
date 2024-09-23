from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class TeamModel(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    base_team = Column(String)
    config = Column(String)
    config_encoded = Column(String)

    # Relationships
    user = relationship('UserModel', back_populates='teams')
    tournaments = relationship(
        'TournamentModel',
        secondary='tournament_team_association',
        back_populates='teams'
    )

    # Relationships to games where this team is left_team or right_team
    left_games = relationship(
        'GameModel',
        back_populates='left_team',
        foreign_keys='GameModel.left_team_id'
    )
    right_games = relationship(
        'GameModel',
        back_populates='right_team',
        foreign_keys='GameModel.right_team_id'
    )

    @property
    def games(self):
        return self.left_games + self.right_games

    def __repr__(self):
        return (f"<TeamModel(id={self.id}, name={self.name}, user_id={self.user_id}, "
                f"base_team={self.base_team}, config={self.config})>")
