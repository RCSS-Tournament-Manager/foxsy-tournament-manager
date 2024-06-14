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


# example
# def handle_message(message_json: dict):
#     message_type = message_json["type"]
#     if message_type == "add_game":
#         message = AddGameMessage(**message_json)
#         return process_add_game(message)
#     elif message_type == "stop_game":
#         message = StopGameMessage(**message_json)
#         return process_stop_game(message)
#     elif message_type == "get_games":
#         message = GetGamesMessage(**message_json)
#         return process_get_games(message)
#     else:
#         raise ValueError(f"Invalid message type: {message_type}")
#
# def process_add_game(message: AddGameMessage):
#     # do something with message.game_info
#     return AddGameResponse(game_id=1, status="starting", success=True)
#
# def process_stop_game(message: StopGameMessage):
#     # do something with message.game_id
#     return StopGameResponse(game_id=1, status="finished")
#
# def process_get_games(message: GetGamesMessage):
#     # do something to get the games
#     return GetGamesResponse(games={"1": "starting", "2": "running"})
#
# # example
# message_json = {
#     "type": "add_game",
#     "game_info": {
#         "game_id": 1,
#         "left_team_name": "team1",
#         "right_team_name": "team2",
#         "left_team_config_id": 1,
#         "right_team_config_id": 2,
#         "left_base_team_name": "helios",
#         "right_base_team_name": "hermes",
#         "server_config": ""
#     }
# }
#
# response = handle_message(message_json)
# print(response)
#
# message_json = {
#     "type": "stop_game",
#     "game_id": 1
# }
#
# response = handle_message(message_json)
#
# print(response)
#
# message_json = {
#     "type": "get_games"
# }
#
# response = handle_message(message_json)
#
# print(response)
