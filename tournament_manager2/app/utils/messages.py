from pydantic import BaseModel, Field
from typing import Optional


class BaseMessage(BaseModel):
    pass

class TeamMessage(BaseModel):
    user_id: int = Field(None, example=1)
    team_id: Optional[int] = Field(None, example=1)
    team_name: str = Field(None, example="team1")
    team_config_json: Optional[str] = Field(None, example='{"team_config_json": "{\"version\":1, \"formation_name\":\"433l\"}"}')
    base_team_name: str = Field(None, example="cyrus")

    def fix_json(self):
        if self.team_config_json:
            self.team_config_json = self.team_config_json.replace(' ', '')
            self.team_config_json = self.team_config_json.replace('\r\n', '')
            self.team_config_json = self.team_config_json.replace('\r', '')
            self.team_config_json = self.team_config_json.replace("'", '"')


class AddTournamentRequestMessage(BaseMessage):
    tournament_name: str = Field(None, example="RoboCup 2024")
    start_at: str = Field(None, example="2024-07-01")
    user_id: int = Field(None, example=1)
    teams: list[TeamMessage] = Field(None, example=[{"user_id": 1, "team_name": "team1", "team_config_json": '{"team_config_json": "{\"version\":1, \"formation_name\":\"433l\"}"}', "base_team_name": "cyrus"}])
    # example:
    # {
    #     "tournament_name": "RoboCup 2024",
    #     "start_at": "2024-07-01",
    #     "user_id": 1,
    #     "teams": [
    #         {"user_id": 1,"team_name": "team1","team_config_json": '{"team_config_json": "{\"version\":1, \"formation_name\":\"433l\"}"}',"base_team_name": "cyrus"},
    #         {"user_id": 2,"team_name": "team2","team_config_json": '{"team_config_json": "{\"version\":1, \"formation_name\":\"433l\"}"}',"base_team_name": "cyrus"},
    #         {"user_id": 3,"team_name": "team3","team_config_json": '{"team_config_json": "{\"version\":1, \"formation_name\":\"433l\"}"}',"base_team_name": "cyrus"}
    #     ]
    # }


class AddTournamentResponseMessage(BaseModel):
    tournament_id: Optional[int] = Field(None, example=1)
    success: bool = Field(None, example=True)
    error: Optional[str] = Field(None, example="")


class GameMessage(BaseModel):
    game_id: int = Field(None, example=1)
    left_team_id: int = Field(None, example=1)
    right_team_id: int = Field(None, example=2)
    status: str = Field(None, example="pending")

class TournamentMessage(BaseModel):
    tournament_id: int = Field(None)
    tournament_name: str = Field(None)
    start_at: str = Field(None)
    user_id: int = Field(None)
    teams: list[TeamMessage] = Field(None)
    games: list[GameMessage] = Field(None)

class AddGameResponse(BaseModel):
    game_id: int = Field(None, example=1)
    status: str = Field(None, example="starting")
    success: bool = Field(None, example=True)
    error: Optional[str] = Field(None, example="")
    port: Optional[int] = Field(None, example=12345)


class GameInfoSummary(BaseModel):
    game_id: int = Field(None, example=1)
    status: str = Field(None, example="starting")
    port: Optional[int] = Field(None, example=12345)
    left_score: Optional[int] = Field(None, example=-1)
    right_score: Optional[int] = Field(None, example=-1)
    left_penalty: Optional[int] = Field(None, example=-1)
    right_penalty: Optional[int] = Field(None, example=-1)


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
    server_config: str = Field(None, example="--server::port=6000")

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


class RegisterMessage(BaseMessage):
    ip: str = Field(None, example="localhost")
    port: int = Field(None, example=12345)
    available_games_count: int = Field(None, example=2)