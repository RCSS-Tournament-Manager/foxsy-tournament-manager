from datetime import datetime
from enum import Enum
from typing import Optional, Union
from sqlmodel import Field, SQLModel

class GameStatus(Enum):
    WAITING = "Waiting"
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    FINISHED = "Finished"

class Game(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tournament_id: Optional[int] = Field(default=None, foreign_key="tournament.id")
    team_left_id: Optional[int] = Field(default=None, foreign_key="team.id")
    team_right_id: Optional[int] = Field(default=None, foreign_key="team.id")
    start_time: Union[datetime, None]
    end_time: Union[datetime, None]
    status: GameStatus
    order: int