import traceback
from fastapi import FastAPI, HTTPException, Security, Depends
import uvicorn
from typing import Union
from managers.tournament_manager import TournamentManager
from managers.team_manager import TeamManager
from managers.user_manager import UserManager
from managers.database_manager import DatabaseManager
from managers.runner_manager import RunnerManager
from models.runner_log_model import RunnerLogModel

from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from utils.messages import *
import logging
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, List
from storage.minio_client import MinioClient

from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

description = """
Welcome to the **Tournament Manager API**! This API allows you to manage tournaments, teams, games, and runners seamlessly.

## Features
- **Users**: Register and manage users.
- **Teams**: Register and manage teams participating in tournaments.
- **Tournaments**: Create, update, and manage tournaments.
- **Games**: Start, finish, and monitor games within tournaments.
- **Runners**: Register runners, send commands, and monitor runner logs.

## Getting Started
To get started with the Tournament Manager API, you'll need to obtain an API key and include it in your requests.

## Contact
For any inquiries or support, please contact:
- **Email**: contact@foxsy.ai
- **GitHub**: [TournamentManager](https://github.com/RCSS-Tournament-Manager/foxsy-tournament-manager)
"""

class FastApiApp:
    def __init__(self, db_manager: DatabaseManager, minio_client: MinioClient, api_key: str, api_key_name: str = "api_key", port: int = 8000):
        self.logger = logging.getLogger(__name__)
        self.app = FastAPI(
            title="Tournament Manager API",
            version="0.1.0",
            description=description,
            terms_of_service='https://drive.google.com/file/d/1bwmAuBHYOUQUA2z0Gw8bj7XKaLXaYtOc/view',
            contact={
                "name": "Foxsy Support",
                "url": "https://foxsy.ai/",
                "email": "contact@foxsy.ai",
            },
            license_info={
                "name": "Apache 2.0",
                "url": "https://foxsy.ai",
            },
            redoc_url="/redoc",
            docs_url=None, 
            )
        self.db_manager = db_manager
        self.minio_client = minio_client
        self.api_key = api_key
        self.api_key_name = api_key_name
        self.port = port
        self.game_log_tmp_path = "/app/game_log_tmp"

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allow all methods
            allow_headers=["*"],  # Allow all headers
        )

        # Mount static files
        self.is_static_mounted = False
        try:
            self.app.mount("/static", StaticFiles(directory="app/static"), name="static")
            self.is_static_mounted = True
            self.logger.info(f"Static files mounted: {self.is_static_mounted}")
        except Exception as e:
            self.is_static_mounted = False
            self.logger.error(f"Failed to mount static files: {e}")
            

        self.setup_routes()

    def setup_routes(self):
        api_key_header = APIKeyHeader(name=self.api_key_name, auto_error=False)

        async def get_api_key(api_key: str = Security(api_key_header)):
            if api_key == self.api_key:
                return api_key
            else:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
                )
        
                # Define dependencies inside the setup_routes method to access self.db_manager
        async def get_db() -> AsyncGenerator[AsyncSession, None]:
            async for session in self.db_manager.get_session():
                yield session

        def get_tournament_manager(
            db_session: AsyncSession = Depends(get_db)
        ) -> TournamentManager:
            return TournamentManager(
                db_session=db_session,
                minio_client=self.minio_client
            )
            
        def get_team_manager(
            db_session: AsyncSession = Depends(get_db)
        ) -> TeamManager:
            return TeamManager(
                db_session=db_session
            )
            
        def get_user_manager(
            db_session: AsyncSession = Depends(get_db)
        ) -> UserManager:
            return UserManager(
                db_session=db_session
            )
            
        def get_runner_manager(
            db_session: AsyncSession = Depends(get_db)
        ) -> RunnerManager:
            return RunnerManager(
                db_session=db_session
            )

        @self.app.get("/", tags=["Health Check"], include_in_schema=False)
        def read_root():
            return {"message": "Welcome to the Tournament Manager API. Visit /docs or /redoc for API documentation."}
        @self.app.get("/api-check", tags=["Health Check"])
        def read_root2():
            return {"message": "Hello World"}


        @self.app.post("/user/add" , response_model=ResponseMessage, tags=["User Management"])
        async def add_user(message_json: AddUserRequestMessage, 
                           user_manager: UserManager = Depends(get_user_manager),
                           api_key: str = Depends(get_api_key)):
            self.logger.info(f"add_user: {message_json}")
            try:
                message = message_json
                AddUserRequestMessage.model_validate(message.model_dump())
                self.logger.info(f"add_user: adding message to manager: {message}")
                return await user_manager.add_user(message)
            except Exception as e:
                self.logger.error(f"add_user: {e}")
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/user/get", response_model=Union[ResponseMessage, GetUserResponseMessage], tags=["User Management"])
        async def get_user(message_json: GetUserRequestMessage,
                           user_manager: UserManager = Depends(get_user_manager),
                           api_key: str = Depends(get_api_key)) -> Union[ResponseMessage, GetUserResponseMessage]:
            self.logger.info(f"get_user: {message_json}")
            try:
                message = message_json
                GetUserRequestMessage.model_validate(message.model_dump())
                if message.is_empty():
                    raise Exception("GetUserRequestMessage is empty")

                res = GetUserResponseMessage()
                return await user_manager.get_user_info(message)
            except Exception as e:
                self.logger.error(f"get_user: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.get("/user/get_all", response_model=Union[ResponseMessage, GetUsersResponseMessage], tags=["User Management"])
        async def get_users(user_manager: UserManager = Depends(get_user_manager),
                            api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_users")
            try:
                return await user_manager.get_users()
            except Exception as e:
                self.logger.error(f"get_users: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/team/add", response_model=Union[GetTeamResponseMessage, ResponseMessage], tags=["Team Management"])
        async def add_team(message_json: AddTeamRequestMessage,
                           team_manager: TeamManager = Depends(get_team_manager),
                           user_manager: UserManager = Depends(get_user_manager),
                           api_key: str = Depends(get_api_key)):
            self.logger.info(f"add_team: {message_json}")
            try:
                message = message_json
                AddTeamRequestMessage.model_validate(message.model_dump())
                user = await user_manager.get_user_or_create(message.user_code)
                self.logger.info(f"add_team: adding message to manager: {message}")
                return await team_manager.create_team(message)
            except Exception as e:
                self.logger.error(f"add_team: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/team/get", response_model=Union[GetTeamResponseMessage, ResponseMessage], tags=["Team Management"]) # TODO merge GetTeamResponseMessage and TeamMessage
        async def get_team(message_json: GetTeamRequestMessage,
                           team_manager: TeamManager = Depends(get_team_manager),
                           user_manager: UserManager = Depends(get_user_manager),
                           api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_team: {message_json}")
            try:
                message = message_json
                GetTeamRequestMessage.model_validate(message.model_dump())
                user = await user_manager.get_user_or_create(message.user_code)
                self.logger.info(f"get_team: adding message to manager: {message}")
                return await team_manager.get_team(message)
            except Exception as e:
                self.logger.error(f"get_team: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/team/get_all", response_model=Union[ResponseMessage, GetTeamsResponseMessage], tags=["Team Management"])
        async def get_teams(team_manager: TeamManager = Depends(get_team_manager),
                            user_manager: UserManager = Depends(get_user_manager),
                            api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_teams")
            try:
                return await team_manager.get_teams()
            except Exception as e:
                self.logger.error(f"get_teams: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/team/remove", response_model=ResponseMessage, tags=["Team Management"])
        async def remove_team(message_json: RemoveTeamRequestMessage,
                              team_manager: TeamManager = Depends(get_team_manager),
                              user_manager: UserManager = Depends(get_user_manager),
                              api_key: str = Depends(get_api_key)):
            self.logger.info(f"remove_team: {message_json}")
            try:
                message = message_json
                RemoveTeamRequestMessage.model_validate(message.model_dump())
                user = await user_manager.get_user_or_create(message.user_code)
                self.logger.info(f"remove_team: adding message to manager: {message}")
                return await team_manager.remove_team(message)
            except Exception as e:
                self.logger.error(f"remove_team: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/team/update", response_model=Union[GetTeamResponseMessage, ResponseMessage], tags=["Team Management"])
        async def update_team(message_json: UpdateTeamRequestMessage,
                              team_manager: TeamManager = Depends(get_team_manager),
                              user_manager: UserManager = Depends(get_user_manager),
                              api_key: str = Depends(get_api_key)):
            self.logger.info(f"update_team: {message_json}")
            try:
                message = message_json
                UpdateTeamRequestMessage.model_validate(message.model_dump())
                user = await user_manager.get_user_or_create(message.user_code)
                self.logger.info(f"update_team: adding message to manager: {message}")
                return await team_manager.update_team(message)
            except Exception as e:
                self.logger.error(f"update_team: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/tournament/add", response_model=ResponseMessage, tags=["Tournament Management"])
        async def add_tournament(message_json: AddTournamentRequestMessage,
                                 tournament_manager: TournamentManager = Depends(get_tournament_manager),
                                 user_manager: UserManager = Depends(get_user_manager),
                                 api_key: str = Depends(get_api_key)):
            self.logger.info(f"add_tournament: {message_json}")
            try:
                message = message_json
                AddTournamentRequestMessage.model_validate(message.model_dump())
                user = await user_manager.get_user_or_create(message.user_code)
                self.logger.info(f"add_tournament: adding message to manager: {message}")
                return await tournament_manager.add_tournament(message)
            except Exception as e:
                self.logger.error(f"add_tournament: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.get("/tournament/get/{tournament_id}", response_model=Union[TournamentMessage, ResponseMessage], tags=["Tournament Management"])
        async def get_tournament(tournament_id: int,
                                 tournament_manager: TournamentManager = Depends(get_tournament_manager),
                                 api_key: str = Depends(get_api_key)):
            try:
                self.logger.info(f"get_tournament: {tournament_id}")
                res = await tournament_manager.get_tournament(tournament_id)
                self.logger.info(f"get_tournament: {res}")
                return res
            except Exception as e:
                self.logger.error(f"get_tournament: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/tournament/get_all", response_model=Union[ResponseMessage, GetTournamentsResponseMessage], tags=["Tournament Management"])
        async def get_tournaments(tournament_manager: TournamentManager = Depends(get_tournament_manager),
                                  api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_tournaments")
            try:
                return await tournament_manager.get_tournaments()
            except Exception as e:
                self.logger.error(f"get_tournaments: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/tournament/register_team", response_model=ResponseMessage, tags=["Tournament Management"])
        async def register_team(message_json: RegisterTeamInTournamentRequestMessage,
                                tournament_manager: TournamentManager = Depends(get_tournament_manager),
                                team_manager: TeamManager = Depends(get_team_manager),
                                user_manager: UserManager = Depends(get_user_manager),
                                api_key: str = Depends(get_api_key)):
            self.logger.info(f"register_team: {message_json}")
            try:
                message = message_json
                RegisterTeamInTournamentRequestMessage.model_validate(message.model_dump())
                user = await user_manager.get_user_or_create(message.user_code)
                self.logger.info(f"register_team: adding message to manager: {message}")
                return await tournament_manager.register_team_in_tournament(message)
            except Exception as e:
                self.logger.error(f"register_team: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/tournament/remove_team", response_model=ResponseMessage, tags=["Tournament Management"]) # TODO Add Test
        async def remove_team_from_tournament(message_json: RemoveTeamFromTournamentRequestMessage,
                                                tournament_manager: TournamentManager = Depends(get_tournament_manager),
                                                team_manager: TeamManager = Depends(get_team_manager),
                                                user_manager: UserManager = Depends(get_user_manager),
                                                api_key: str = Depends(get_api_key)):
                self.logger.info(f"remove_team_from_tournament: {message_json}")
                try:
                    message = message_json
                    RemoveTeamFromTournamentRequestMessage.model_validate(message.model_dump())
                    user = await user_manager.get_user_or_create(message.user_code)
                    self.logger.info(f"remove_team_from_tournament: adding message to manager: {message}")
                    return await tournament_manager.remove_team_from_tournament(message)
                except Exception as e:
                    self.logger.error(f"remove_team_from_tournament: {e}")
                    traceback.print_exc()
                    return ResponseMessage(success=False, error=str(e))
                
        @self.app.post("/tournament/update", response_model=ResponseMessage, tags=["Tournament Management"])
        async def update_tournament(message_json: UpdateTournamentRequestMessage,
                                    tournament_manager: TournamentManager = Depends(get_tournament_manager),
                                    user_manager: UserManager = Depends(get_user_manager),
                                    api_key: str = Depends(get_api_key)):
            self.logger.info(f"update_tournament: {message_json}")
            try:
                message = message_json
                UpdateTournamentRequestMessage.model_validate(message.model_dump())
                self.logger.info(f"update_tournament: adding message to manager: {message}")
                return await tournament_manager.update_tournament(message)
            except Exception as e:
                self.logger.error(f"update_tournament: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/game/add_friendly_game", response_model=ResponseMessage, tags=["Game Management"])
        async def add_friendly_game(message_json: AddFriendlyGameRequestMessage,
                                    tournament_manager: TournamentManager = Depends(get_tournament_manager),
                                    user_manager: UserManager = Depends(get_user_manager),
                                    api_key: str = Depends(get_api_key)):
            self.logger.info(f"add_friendly_game: {message_json}")
            try:
                message = message_json
                AddFriendlyGameRequestMessage.model_validate(message.model_dump())
                self.logger.info(f"add_friendly_game: adding message to manager: {message}")
                return await tournament_manager.add_friendly_game(message)
            except Exception as e:
                self.logger.error(f"add_friendly_game: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))
            
        @self.app.get("/game/get/{game_id}", response_model=Union[GameMessage, ResponseMessage], tags=["Game Management"])
        async def get_game(game_id: int,
                           tournament_manager: TournamentManager = Depends(get_tournament_manager),
                           api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_game: {game_id}")
            res = await tournament_manager.get_game(game_id)
            self.logger.info(f"get_game: {res}")
            return res

        @self.app.get("/game/download_log/{game_id}", tags=["Game Management"])
        async def download_log(game_id: int,
                               tournament_manager: TournamentManager = Depends(get_tournament_manager)):
            self.logger.info(f"download_log: {game_id}")
            game_log_name = f"{game_id}.zip"
            tmp_file_path = os.path.join("/tmp", game_log_name)
            try:
                res = await tournament_manager.download_log_file(game_id, tmp_file_path)
                if not res:
                    raise Exception(f"File not found: {game_id}")
                if not os.path.exists(tmp_file_path):
                    raise Exception(f"File not found: {tmp_file_path}")
                return FileResponse(tmp_file_path, media_type="application/octet-stream", filename=game_log_name)
            except Exception as e:
                raise HTTPException(status_code=404, detail=f"File not found or {e}") from e

        @self.app.get("/game/tmp_get_url/{game_id}", response_model=dict, tags=["Game Management"])
        async def tmp_get_url(game_id: int,
                              tournament_manager: TournamentManager = Depends(get_tournament_manager),
                              api_key: str = Depends(get_api_key)) -> dict:
            self.logger.info(f"tmp_get_url: {game_id}")
            game_log_tmp_path = self.game_log_tmp_path
            if not os.path.exists(game_log_tmp_path):
                os.makedirs(game_log_tmp_path)
            game_log_name = f"{game_id}"
            tmp_file_path = os.path.join(game_log_tmp_path, f"{game_log_name}.zip")
            tmp_dir_path = os.path.join(game_log_tmp_path, game_log_name)

            if not os.path.exists(tmp_file_path):
                self.logger.debug(f"downloading log file: {game_id} to {tmp_file_path}")
                try:
                    res = await tournament_manager.download_log_file(game_id, tmp_file_path)
                    if not res:
                        raise Exception(f"File not found: {game_id}")
                    if not os.path.exists(tmp_file_path):
                        raise Exception(f"File not found: {tmp_file_path}")

                except Exception as e:
                    raise HTTPException(status_code=404, detail=f"File not found or {e}") from e

                import zipfile

                self.logger.debug(f"unzipping file: {tmp_file_path} to {tmp_dir_path}")
                with zipfile.ZipFile(tmp_file_path, 'r') as zip_ref:
                    zip_ref.extractall(tmp_dir_path)

                if not os.path.exists(tmp_dir_path):
                    raise Exception(f"Dir not found: {tmp_dir_path}")

            path = tmp_dir_path
            files = os.listdir(path)
            rcg_file_name = None
            for file in files:
                if file.endswith('.rcg'):
                    rcg_file_name = file
                    break
            if rcg_file_name is None:
                raise HTTPException(status_code=404, detail=f"File not found: {game_id}")
            url = f'http://165.22.28.139/JaSMIn/player.html?replay=http://165.22.28.139/gamelog/{game_id}/{rcg_file_name}'
            return {"url": url}


        @self.app.get("/runner/get/{runner_id}", response_model=GetRunnerResponseMessage, tags=["Runner Management"])
        async def get_runner(
            runner_id: int,
            runner_manager: RunnerManager = Depends(get_runner_manager),
            api_key: str = Depends(get_api_key)
        ):
            self.logger.info(f"get_runner: {runner_id}")
            try:
                runner = await runner_manager.get_runner(runner_id)
                if not runner:
                    raise HTTPException(status_code=404, detail="Runner not found")
                self.logger.info(f"get_runner: {runner}")
                return runner
            except HTTPException as he:
                raise he
            except Exception as e:
                self.logger.error(f"get_runner: {e}")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/runner/get_all", response_model=GetAllRunnersResponseMessage, tags=["Runner Management"])
        async def get_all_runners(
            runner_manager: RunnerManager = Depends(get_runner_manager),
            api_key: str = Depends(get_api_key)
        ):
            self.logger.info("get_all_runners")
            try:
                runners = await runner_manager.get_all_runners()
                self.logger.info(f"get_all_runners: Retrieved {len(runners.runners)} runners")
                return runners
            except Exception as e:
                self.logger.error(f"get_all_runners: {e}")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/runner/get_log/{runner_id}", response_model=GetRunnerLogResponseMessage, tags=["Runner Management"])
        async def get_runner_log(
            runner_id: int,
            runner_manager: RunnerManager = Depends(get_runner_manager),
            api_key: str = Depends(get_api_key)
        ):
            self.logger.info(f"get_runner_log: {runner_id}")
            try:
                logs = await runner_manager.get_runner_logs(runner_id)
                if not logs:
                    raise HTTPException(status_code=404, detail="No logs found for the runner")
                self.logger.info(f"get_runner_log: Retrieved {len(logs)} logs for runner {runner_id}")
                return GetRunnerLogResponseMessage(logs=logs)
            except HTTPException as he:
                raise he
            except Exception as e:
                self.logger.error(f"get_runner_log: {e}")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/runner/send_command", response_model=AnyResponseMessage, tags=["Runner Management"])
        async def send_command(
            command_request: SendCommandRequest,
            runner_manager: RunnerManager = Depends(get_runner_manager),
            api_key: str = Depends(get_api_key)
        ):
            """
            - If runner_ids is None, the command is sent to all runners.
            - If runner_ids is an int or a list of ints, the command is sent to that specific runners.
            - If runner_ids is empty or contains invalid IDs, appropriate errors are returned.
            """
            self.logger.info(f"send_command: {command_request}")
            valid_commands = ["stop", "pause", "resume", "update", "hello"]
            if command_request.command not in valid_commands:
                self.logger.error(f"send_command: Invalid command: {command_request.command}")
                return AnyResponseMessage(success=False, value="Invalid command.")
            try:
                runners_ids = command_request.runner_ids if command_request.runner_ids else []
                if isinstance(command_request.runner_ids, int):
                    runners_ids = [command_request.runner_ids]
                
                responses = await runner_manager.send_command_to_runners(runners_ids, command_request)
                return AnyResponseMessage(success=True, value=responses, error=None)
            except Exception as e:
                self.logger.exception(f"send_command: Unexpected error: {e}")
                traceback.print_exc()
                return AnyResponseMessage(success=False, error=str(e))

        @self.app.post("/from_runner/game_started", response_model=ResponseMessage, tags=["Runner Management"])
        async def game_started(
            json: GameStartedMessage,
            runner_manager: RunnerManager = Depends(get_runner_manager),
            api_key: str = Depends(get_api_key)
        ):
            self.logger.info(f"game_started: {json}")
            try:
                response = await runner_manager.handle_game_started(json)
                return response
            except Exception as e:
                self.logger.error(f"game_started: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/from_runner/game_finished", response_model=ResponseMessage, tags=["Runner Management"])
        async def game_finished(
            json: GameFinishedMessage,
            runner_manager: RunnerManager = Depends(get_runner_manager),
            api_key: str = Depends(get_api_key)
        ):
            self.logger.info(f"game_finished: {json}")
            try:
                response = await runner_manager.handle_game_finished(json)
                return response
            except Exception as e:
                self.logger.error(f"game_finished: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/from_runner/register", response_model=ResponseMessage, tags=["Runner Management"])
        async def runner_register(
            json: RegisterGameRunnerRequest,
            runner_manager: RunnerManager = Depends(get_runner_manager),
            api_key: str = Depends(get_api_key)
        ):
            self.logger.info(f"runner_register: {json}")
            try:
                return await runner_manager.register(json)
            except Exception as e:
                self.logger.error(f"runner_register: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/from_runner/submit_log", response_model=ResponseMessage, tags=["Runner Management"])
        async def submit_runner_log(
            log: SubmitRunnerLog,
            runner_manager: RunnerManager = Depends(get_runner_manager),
            api_key: str = Depends(get_api_key)
        ):
            self.logger.info(f"submit_runner_log: {log}")
            try:
                # check if runner exists
                runner = await runner_manager.get_runner(log.runner_id)
                if not runner:
                    self.logger.error(f"Runner with id {log.runner_id} not found")
                    raise HTTPException(status_code=404, detail="Runner not found")

                # RunnerLogModel instance
                new_log = RunnerLogModel(
                    runner_id=log.runner_id,
                    message=log.message,
                    log_level=log.log_level,
                    timestamp=datetime.fromisoformat(log.timestamp) # or datetime.utcnow()
                )

                runner_manager.db_session.add(new_log)
                await runner_manager.db_session.commit()

                self.logger.info(f"Log submitted for runner {log.runner_id}")
                return ResponseMessage(success=True, error=None)
            except HTTPException as he:
                raise he
            except Exception as e:
                self.logger.error(f"submit_runner_log: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))

        @self.app.post("/from_runner/status_update", response_model=ResponseMessage, tags=["Runner Management"])
        async def status_update(
            status_message: RunnerStatusMessage,
            runner_manager: RunnerManager = Depends(get_runner_manager),
            api_key: str = Depends(get_api_key)
        ):
            self.logger.info(f"status_update: {status_message}")
            try:
                response = await runner_manager.handle_status_update(status_message)
                if not response.success:
                    raise HTTPException(status_code=400, detail=response.error)
                return response
            except HTTPException as he:
                raise he
            except Exception as e:
                self.logger.error(f"status_update: {e}")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=str(e))
            
        @self.app.get("/docs", include_in_schema=False)
        async def custom_swagger_ui_html():
            if self.is_static_mounted:
                try:
                    html_response = get_swagger_ui_html(
                        openapi_url=self.app.openapi_url,
                        title=self.app.title + " - Swagger UI",
                        swagger_favicon_url="/static/icon.png",  
                    )
                    dark_mode_button = '''
                    <button id="dark-mode-toggle" style="
                        position: fixed;
                        top: 10px;
                        right: 10px;
                        padding: 10px 20px;
                        background-color: #ff5722;
                        color: #ffffff;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        z-index: 1000;
                    ">🌙 Dark Mode</button>
                    '''
                    
                    # Inject custom JavaScript before </body>

                    html_str = html_response.body.decode('utf-8')
                    logo = '<img src="/static/icon.png" alt="Foxsy Logo" class="foxsy-logo">'
                    html_str = html_str.replace('</head>', '<style>.foxsy-logo { max-width: 100px; }</style></head>')
                    html_str = html_str.replace('</body>', '<script src="/static/dark_mode.js"></script></body>')
                    html_str = html_str.replace('<div id="swagger-ui">', logo + '<div id="swagger-ui">')
                    html_str = html_str.replace('<div id="swagger-ui">', dark_mode_button + '<div id="swagger-ui">')
                except Exception as e:
                    self.logger.info(f"custom_swagger_ui_html: {e}")
                    html_str = get_swagger_ui_html(
                        openapi_url=self.app.openapi_url,
                        title=self.app.title + " - Swagger UI",
                    ).body.decode('utf-8')
                return HTMLResponse(content=html_str, media_type="text/html")
            else:
                return get_swagger_ui_html(
                    openapi_url=self.app.openapi_url,
                    title=self.app.title + " - Swagger UI",
                )


    async def run(self):
        self.logger.info('Starting FastAPI app')
        config = uvicorn.Config(self.app, host="0.0.0.0", port=self.port)
        server = uvicorn.Server(config)
        await server.serve()