from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from .base import Base

class TournamentStatus:
    WAIT_FOR_REGISTRATION = 'wait_for_registration'
    REGISTRATION = 'registration'
    WAIT_FOR_START = 'wait_for_start'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'

# Association table for participants
tournament_participants_association = Table(
    'tournament_participants_association', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('tournament_id', Integer, ForeignKey('tournaments.id'))
)

class TournamentModel(Base):
    __tablename__ = 'tournaments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey('users.id'))  # Correct ForeignKey for the owner
    start_at = Column(DateTime)
    start_registration_at = Column(DateTime)
    end_registration_at = Column(DateTime)
    done = Column(Boolean, default=False)
    status = Column(String, default=TournamentStatus.WAIT_FOR_REGISTRATION)

    # Relationships
    owner = relationship('UserModel', back_populates='owned_tournaments')  # Tournament owner
    
    participants = relationship(
        'UserModel',
        secondary=tournament_participants_association,
        back_populates='participating_tournaments'
    )  # Users participating in this tournament

    teams = relationship(
        'TeamModel',
        secondary='tournament_team_association',
        back_populates='tournaments',
        cascade='all, delete'
    )

    games = relationship('GameModel', back_populates='tournament', cascade='all, delete-orphan')

    def __repr__(self):
        return (f"<TournamentModel(id={self.id}, name={self.name}, owner_id={self.owner_id}, "
                f"start_at={self.start_at}])>")