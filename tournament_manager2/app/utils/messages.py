from pydantic import BaseModel, Field
from typing import Optional, Union, List
from datetime import datetime
from enum import Enum


class GameStatusMessageEnum(str, Enum):
    PENDING = "pending"
    IN_QUEUE = "in_queue"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"

class LogLevelMessageEnum(str, Enum):
    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'

class RunnerStatusMessageEnum(str, Enum):
    RUNNING = 'running'
    PAUSED = 'paused'
    UNKNOWN = 'unknown'
    CRASHED = 'crashed'

class BaseMessage(BaseModel):
    pass

class RegisterGameRunnerRequest(BaseMessage):
    ip: str = Field(None, example="localhost")
    port: int = Field(None, example=12345)
    available_games_count: int = Field(None, example=2)

def fix_json(json_str):
    if json_str:
        json_str = json_str.replace(' ', '')
        json_str = json_str.replace('\r\n', '')
        json_str = json_str.replace('\r', '')
        json_str = json_str.replace("'", '"')
    return json_str

def encode_json(json_str):
    # replace single quotes with @q@
    # replace double quotes with @qq@
    # replace comma with @c@
    fix_json(json_str)
    json_str = json_str.replace("'", "@q@")
    json_str = json_str.replace('"', "@qq@")
    json_str = json_str.replace(',', "@c@")
    return json_str

class GameInfoMessage(BaseModel):
    game_id: int = Field(None, example=1)
    left_team_name: str = Field(None, example="team1")
    right_team_name: str = Field(None, example="team2")
    left_team_config_id: Optional[int] = Field(None, example=1)
    right_team_config_id: Optional[int] = Field(None, example=2)
    left_team_config_json: Optional[str] = Field(None, example='"{\"version\":1, \"formation_name\":\"433\"}"')
    right_team_config_json: Optional[str] = Field(None, example='"{\"version\":1, \"formation_name\":\"433\"}"')
    left_team_config_json_encoded: Optional[str] = Field(None, example='{@qq@version@qq@:1@c@@qq@formation_name@qq@:@qq@433@qq@}')
    right_team_config_json_encoded: Optional[str] = Field(None, example='{@qq@version@qq@:1@c@@qq@formation_name@qq@:@qq@433@qq@}')
    left_base_team_name: str = Field(None, example="cyrus")
    right_base_team_name: str = Field(None, example="cyrus")
    server_config: Optional[str] = Field(None, example="--server::auto_mode=true")

    def fix_json(self):
        if self.left_team_config_json:
            self.left_team_config_json = fix_json(self.left_team_config_json)
        if self.right_team_config_json:
            self.right_team_config_json = fix_json(self.right_team_config_json)

class GameStartedMessage(BaseModel):
    game_id: int = Field(None, example=1)
    success: bool = Field(None, example=True)
    runner_id: Optional[int] = Field(None, example=1)
    error: Optional[str] = Field(None, example="")
    port: Optional[int] = Field(None, example=12345)

class StopGameResponse(BaseModel): # TODO remove?
    game_id: Optional[int] = Field(None, example=1)
    game_port: Optional[int] = Field(None, example=12345)
    success: bool = Field(None, example=True)
    error: Optional[str] = Field(None, example="")

class GameFinishedMessage(BaseModel):
    game_id: int = Field(None, example=1)
    left_score: Optional[int] = Field(None, example=-1)
    right_score: Optional[int] = Field(None, example=-1)
    left_penalty: Optional[int] = Field(None, example=-1)
    right_penalty: Optional[int] = Field(None, example=-1)
    runner_id: Optional[int] = Field(None, example=1)
    success: bool = Field(None, example=True)

class GetGamesResponse(BaseModel):
    games: list[GameFinishedMessage] = Field(None, example=[{"game_id": 1, "status": "starting", "port": 12345}])

class TeamMessage(BaseModel):
    user_id: int = Field(None, example=1)
    team_id: Optional[int] = Field(None, example=1)
    team_name: str = Field(None, example="team1")
    team_config_json: Optional[str] = Field(None, example='"{\"version\":1, \"formation_name\":\"433\"}"')
    base_team_name: str = Field(None, example="cyrus")

    def fix_json(self):
        if self.team_config_json:
            fix_json(self.team_config_json)

    def encode_json(self):
        if self.team_config_json:
            return encode_json(self.team_config_json)

class AddTournamentRequestMessage(BaseMessage):
    user_code: str = Field(None, example="123456")
    tournament_name: str = Field(None, example="RoboCup 2024")
    start_registration_at: datetime = Field(None, example="2025-10-01 00:00:00")
    end_registration_at: datetime = Field(None, example="2025-11-30 00:00:00")
    start_at: datetime = Field(None, example="2025-12-01 00:00:00")
    
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
    start_registration_at: datetime = Field(None, example="2024-06-01 00:00:00")
    end_registration_at: datetime = Field(None, example="2024-06-30 00:00:00")
    start_at: datetime = Field(None, example="2024-07-01 00:00:00")
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
    team_config_json: Optional[str] = Field(None, example='"{\"version\":1, \"formation_name\":\"433\"}"')
    
    def fix_json(self):
        if self.team_config_json:
            fix_json(self.team_config_json)

    def encode_json(self):
        if self.team_config_json:
            return encode_json(self.team_config_json)
        return None


class GetTeamRequestMessage(BaseMessage):
    user_code: Optional[str] = Field(None, example="123456")
    team_id: Optional[int] = Field(None, example=1)
    team_name: Optional[str] = Field(None, example="team1")
    
class GetTeamResponseMessage(BaseModel):
    team_id: Optional[int] = Field(None, example=1)
    team_name: str = Field(None, example="team1")
    base_team_name: str = Field(None, example="cyrus")
    team_config_json: Optional[str] = Field(None, example='"{\"version\":1, \"formation_name\":\"433\"}"')
    team_config_json_encoded: Optional[str] = Field(None, example='{@qq@version@qq@:1@c@@qq@formation_name@qq@:@qq@433@qq@}')

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
    error: Optional[str] = Field(None, example="") # why not use error: Union[str, None] = None?
    value: Optional[str] = Field(None, example="")
    # dict: Optional[dict] = Field(None, example={})
    obj: Optional[BaseModel] = Field(None, example={})
    
class GetRunnerResponseMessage(BaseModel):
    id: int
    status: Optional[RunnerStatusMessageEnum] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    address: str
    available_games_count: int

class GetAllRunnersResponseMessage(BaseModel):
    runners: List[GetRunnerResponseMessage]

class RunnerLog(BaseModel):
    log_id: int
    message: str
    timestamp: datetime
    log_level: LogLevelMessageEnum

class GetRunnerLogResponseMessage(BaseModel):
    logs: List[RunnerLog]
    
class SubmitRunnerLog(BaseModel):
    runner_id: int = Field(..., example=1)
    message: str = Field(..., example="Runner encountered an unexpected error.")
    log_level: LogLevelMessageEnum = Field(..., example="ERROR")
    timestamp: Optional[datetime] = Field(None, example="2024-09-18T12:34:56Z")

class UpdateTournamentRequestMessage(BaseModel):
    tournament_id: int = Field(..., example=1)
    start_registration_at: Optional[bool] = Field(None, example=False)
    end_registration_at: Optional[bool] = Field(None, example=False)
    start_at: Optional[bool] = Field(None, example=False)

class SendCommandRequest(BaseModel):
    runner_id: int = Field(..., example=1, description="ID of the runner to send the command to.")
    command: str = Field(..., description="Command to send to the runner.")
    # command_type: RunnerCommandTypeEnum = Field(..., example="start_game", description="Type of command to send.")
    # parameters: Optional[Dict[str, str]] = Field(None, example={"game_id": "42"}, description="Additional parameters for the command.")
    timestamp: Optional[datetime] = Field(None, example="2024-09-18T12:34:56Z", description="Time the command was issued.")
