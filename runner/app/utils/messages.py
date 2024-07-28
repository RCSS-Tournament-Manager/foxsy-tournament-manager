from pydantic import BaseModel, Field
from typing import Optional


class GameStatus(str):
    starting = "starting"
    running = "running"
    finished = "finished"
    error = "error"

class BaseMessage(BaseModel):
    pass

class RegisterMessage(BaseMessage):
    ip: str = Field(None, example="localhost")
    port: int = Field(None, example=12345)
    available_games_count: int = Field(None, example=2)

class RegisterResponse(BaseModel):
    success: bool = Field(None, example=True)
    error: Optional[str] = Field(None, example="")

class GameInfoMessage(BaseModel):
    game_id: int = Field(None, example=1)
    left_team_name: str = Field(None, example="team1")
    right_team_name: str = Field(None, example="team2")
    left_team_config_id: Optional[int] = Field(None, example=1)
    right_team_config_id: Optional[int] = Field(None, example=2)
    left_team_config_json: Optional[str] = Field(None, example='{"left_team_config_json": "{\"version\":1, \"formation_name\":\"433l\"}"}')
    right_team_config_json: Optional[str] = Field(None, example='{"right_team_config_json": "{\"version\":1, \"formation_name\":\"433l\"}"}')
    left_base_team_name: str = Field(None, example="cyrus")
    right_base_team_name: str = Field(None, example="cyrus")
    server_config: Optional[str] = Field(None, example="--server::port=6000")

    def fix_json(self):
        if self.left_team_config_json:
            self.left_team_config_json = self.left_team_config_json.replace(' ', '')
            self.left_team_config_json = self.left_team_config_json.replace('\r\n', '')
            self.left_team_config_json = self.left_team_config_json.replace('\r', '')
            self.left_team_config_json = self.left_team_config_json.replace("'", '"')
        if self.right_team_config_json:
            self.right_team_config_json = self.right_team_config_json.replace(' ', '')
            self.right_team_config_json = self.right_team_config_json.replace('\r\n', '')
            self.right_team_config_json = self.right_team_config_json.replace('\r', '')
            self.right_team_config_json = self.right_team_config_json.replace("'", '"')

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
    left_score: Optional[int] = Field(None, example=-1)
    right_score: Optional[int] = Field(None, example=-1)
    left_penalty: Optional[int] = Field(None, example=-1)
    right_penalty: Optional[int] = Field(None, example=-1)

class GetGamesResponse(BaseModel):
    games: list[GameInfoSummary] = Field(None, example=[{"game_id": 1, "status": "starting", "port": 12345}])
