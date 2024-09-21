from pydantic import BaseModel, Field
from typing import Optional, Union, List
from datetime import datetime


class GameStatus(str):
    starting = "starting"
    running = "running"
    finished = "finished"
    error = "error"

class BaseMessage(BaseModel):
    pass

class RegisterGameRunnerRequest(BaseMessage):
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
    left_team_config_json: Optional[str] = Field(None, example='{"left_team_config_json": "{\"version\":1, \"formation_name\":\"433-433\"}"}')
    right_team_config_json: Optional[str] = Field(None, example='{"right_team_config_json": "{\"version\":1, \"formation_name\":\"433-433\"}"}')
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

class TeamMessage(BaseModel):
    user_id: int = Field(None, example=1)
    team_id: Optional[int] = Field(None, example=1)
    team_name: str = Field(None, example="team1")
    team_config_json: Optional[str] = Field(None, example='{"team_config_json": "{\"version\":1, \"formation_name\":\"433-433\"}"}')
    base_team_name: str = Field(None, example="cyrus")

    def fix_json(self):
        if self.team_config_json:
            self.team_config_json = self.team_config_json.replace(' ', '')
            self.team_config_json = self.team_config_json.replace('\r\n', '')
            self.team_config_json = self.team_config_json.replace('\r', '')
            self.team_config_json = self.team_config_json.replace("'", '"')

class AddTournamentRequestMessage(BaseMessage):
    user_code: str = Field(None, example="123456")
    tournament_name: str = Field(None, example="RoboCup 2024")
    start_at: datetime = Field(None, example="2024-07-01 00:00:00")
    start_registration_at: datetime = Field(None, example="2024-06-01 00:00:00")
    end_registration_at: datetime = Field(None, example="2024-06-30 00:00:00")
    
class RemoveTournamentRequestMessage(BaseMessage):
    user_code: str = Field(None, example="123456")
    tournament_id: int = Field(None, example=1)

class GetTournamentRequestMessage(BaseMessage):
    user_code: str = Field(None, example="123456")
    tournament_id: int = Field(None, example=1)
    
class TournamentTeamResultMessage(BaseModel):
    team_id: int = Field(None)
    team_name: str = Field(None)
    win: int = Field(None)
    lose: int = Field(None)
    draw: int = Field(None)
    scored_goal: int = Field(None)
    received_goal: int = Field(None)
    goal_difference: int = Field(None)
    point: int = Field(None)
    rank: int = Field(None)

class GameMessage(BaseModel):
    game_id: int = Field(None, example=1)
    left_team_id: int = Field(None, example=1)
    right_team_id: int = Field(None, example=2)
    status: str = Field(None, example="pending")
    left_team_score: Optional[int] = Field(None, example=-1)
    right_team_score: Optional[int] = Field(None, example=-1)
    
class TournamentMessage(BaseModel):
    tournament_id: int = Field(None)
    tournament_name: str = Field(None)
    start_at: datetime = Field(None)
    start_registration_at: datetime = Field(None)
    end_registration_at: datetime = Field(None)
    status: str = Field(None)
    user_id: int = Field(None)
    teams: list[TeamMessage] = Field(None)
    games: list[GameMessage] = Field(None)
    results: list[TournamentTeamResultMessage] = Field(None)

class TournamentSummaryMessage(BaseModel):
    tournament_id: int = Field(None, example=1)
    tournament_name: str = Field(None, example="RoboCup 2024")
    start_at: datetime = Field(None, example="2024-07-01 00:00:00")
    start_registration_at: datetime = Field(None, example="2024-06-01 00:00:00")
    end_registration_at: datetime = Field(None, example="2024-06-30 00:00:00")
    status: str = Field(None, example="pending")
    
class GetTournamentsResponseMessage(BaseModel):
    tournaments: list[TournamentSummaryMessage] = Field(None, example=[{"tournament_id": 1, "tournament_name": "RoboCup 2024"}])
    
class AddTournamentResponseMessage(BaseModel):
    tournament_id: Optional[int] = Field(None, example=1)
    success: bool = Field(None, example=True)
    error: Optional[str] = Field(None, example="")

class AddTeamRequestMessage(BaseMessage):
    user_code: str = Field(None, example="123456")
    team_name: str = Field(None, example="team1")
    
class RemoveTeamRequestMessage(BaseMessage):
    user_code: str = Field(None, example="123456")
    team_id: int = Field(None, example=1)
    
class UpdateTeamRequestMessage(BaseMessage):
    user_code: str = Field(None, example="123456")
    team_id: int = Field(None, example=1)
    base_team_name: str = Field(None, example="cyrus")    
    team_config_json: Optional[str] = Field(None, example='{"team_config_json": "{\"version\":1, \"formation_name\":\"433-433\"}"}')
    
    def fix_json(self):
        if self.team_config_json:
            self.team_config_json = self.team_config_json.replace(' ', '')
            self.team_config_json = self.team_config_json.replace('\r\n', '')
            self.team_config_json = self.team_config_json.replace('\r', '')
            self.team_config_json = self.team_config_json.replace("'", '"')
    
class GetTeamRequestMessage(BaseMessage):
    user_code: Optional[str] = Field(None, example="123456")
    team_id: Optional[int] = Field(None, example=1)
    team_name: Optional[str] = Field(None, example="team1")
    
class GetTeamResponseMessage(BaseModel):
    team_id: Optional[int] = Field(None, example=1)
    team_name: str = Field(None, example="team1")
    base_team_name: str = Field(None, example="cyrus")
    team_config_json: Optional[str] = Field(None, example='{"team_config_json": "{\"version\":1, \"formation_name\":\"433-433\"}"}')

class GetTeamsResponseMessage(BaseModel):
    teams: list[TeamMessage] = Field(None, example=[{"team_id": 1, "team_name": "team1", "base_team_name": "cyrus"}])
    
class RegisterUserRequestMessage(BaseModel):
    user_code: str = Field(None, example="123456")
    user_name: str = Field(None, example="user1")
    
class RegisterTeamInTournamentRequestMessage(BaseModel):
    user_code: str = Field(None, example="123456")
    tournament_id: int = Field(None, example=1)
    team_id: int = Field(None, example=1)
    
class RemoveTeamFromTournamentRequestMessage(BaseModel):
    user_code: str = Field(None, example="123456")
    tournament_id: int = Field(None, example=1)
    team_id: int = Field(None, example=1)

class AddUserRequestMessage(BaseModel):
    user_name: str = Field(None, example="user1")
    user_code: str = Field(None, example="123456")
    
class GetUserRequestMessage(BaseModel):
    user_code: Optional[str] = Field(None, example="123456")
    user_id: Optional[int] = Field(None, example=1)
    user_name: Optional[str] = Field(None, example="user1")
    
    def is_empty(self):
        return not any([self.user_code, self.user_id, self.user_name])
    
class GetUserResponseMessage(BaseModel):
    user_id: int = Field(None, example=1)
    user_name: str = Field(None, example="user1")
    owned_tournament_ids: list[int] = Field(None)
    in_tournament_ids: list[int] = Field(None)
    team_ids: list[int] = Field(None)
    
class GetUsersResponseMessage(BaseModel):
    users: list[GetUserResponseMessage] = Field(None, example=[{"user_id": 1, "user_name": "user1"}])
        
class ResponseMessage(BaseModel):
    success: bool = Field(None, example=True)
    error: Optional[str] = Field(None, example="")
    value: Optional[str] = Field(None, example="")

class AddGameResponseModel(BaseModel):
    game_id: int
    runner_id: int

class GameInfoSummaryModel(BaseModel):
    game_id: int
    left_score: int
    right_score: int

class RegisterGameRunnerRequestModel(BaseModel):
    game_id: int
    runner_id: int

class SuccessResponse(BaseModel):
    success: bool
    error: Union[str, None] = None
    
class GetRunnerResponseMessage(BaseModel):
    id: int
    status: str
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    ip: Optional[str]
    port: Optional[int]
    available_games_count: int
    name: str

class GetAllRunnersResponseMessage(BaseModel):
    runners: List[GetRunnerResponseMessage]

class RunnerLog(BaseModel):
    log_id: int
    message: str
    timestamp: datetime

class GetRunnerLogResponseMessage(BaseModel):
    logs: List[RunnerLog]