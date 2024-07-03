from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel

class TeamBase(Enum):
    CYRUS = "Cyrus"
    OXSY = "Oxsy"

class Team(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tournament_id: Optional[int] = Field(default=None, foreign_key="tournament.id")
    team_name: str
    team_base: TeamBase
    config: str