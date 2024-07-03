from typing import Optional
from sqlmodel import Field, SQLModel


class GameResult(SQLModel, table=True):
    game_id: Optional[int] = Field(default=None, foreign_key="game.id", primary_key=True)
    team_left_score: int
    team_right_score: int
    winner_id: Optional[int] = Field(default=None, foreign_key="team.id")