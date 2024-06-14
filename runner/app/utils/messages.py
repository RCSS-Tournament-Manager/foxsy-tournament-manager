from pydantic import BaseModel, Field
from typing import Optional


class GameStatus(str):
    starting = "starting"
    running = "running"
    finished = "finished"
    error = "error"

class BaseMessage(BaseModel):
    pass

class GameInfoMessage(BaseModel):
    game_id: int = Field(None, example=1)
    left_team_name: str = Field(None, example="team1")
    right_team_name: str = Field(None, example="team2")
    left_team_config_id: Optional[int] = Field(None, example=1)
    right_team_config_id: Optional[int] = Field(None, example=2)
    left_team_config_json: Optional[str] = Field(None, example='{"team": "team1"}')
    right_team_config_json: Optional[str] = Field(None, example='{"team": "team2"}')
    left_base_team_name: str = Field(None, example="helios")
    right_base_team_name: str = Field(None, example="hermes")
    server_config: str = Field(None, example="")

class AddGameMessage(BaseMessage):
    game_info: GameInfoMessage = Field(None)

class AddGameResponse(BaseModel):
    game_id: int = Field(None, example=1)
    status: str = Field(None, example="starting")
    success: bool = Field(None, example=True)
    error: Optional[str] = Field(None, example="")
    port: Optional[int] = Field(None, example=12345)

class StopGameResponse(BaseModel):
    game_id: Optional[int] = Field(None, example=1)
    game_port: Optional[int] = Field(None, example=12345)
    success: bool = Field(None, example=True)
    error: Optional[str] = Field(None, example="")

class GameInfoSummary(BaseModel):
    game_id: int = Field(None, example=1)
    status: str = Field(None, example="starting")
    port: Optional[int] = Field(None, example=12345)

class GetGamesResponse(BaseModel):
    games: list[GameInfoSummary] = Field(None, example=[{"game_id": 1, "status": "starting", "port": 12345}])
