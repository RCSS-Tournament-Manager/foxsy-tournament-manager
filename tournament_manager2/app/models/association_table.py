from sqlalchemy import Table, Column, Integer, ForeignKey, UniqueConstraint
from .base import Base

tournament_team_association = Table(
    'tournament_team_association',
    Base.metadata,
    Column('tournament_id', Integer, ForeignKey('tournaments.id', ondelete='CASCADE')),
    Column('team_id', Integer, ForeignKey('teams.id', ondelete='CASCADE')),
    UniqueConstraint('tournament_id', 'team_id', name='uix_tournament_team')
)
