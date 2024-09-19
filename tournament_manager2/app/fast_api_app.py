import traceback
from fastapi import FastAPI, HTTPException, Security, Depends
import uvicorn
from typing import Union
from managers.tournament_manager import TournamentManager
from managers.team_manager import TeamManager
from managers.user_manager import UserManager
from managers.database_manager import DatabaseManager
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



class FastApiApp:
    def __init__(self, db_manager: DatabaseManager, minio_client: MinioClient, api_key: str, api_key_name: str = "api_key", port: int = 8000):
        self.logger = logging.getLogger(__name__)
        self.app = FastAPI()
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
        

        def get_tournament_manager(
            db_session: AsyncSession = Depends(self.db_manager.get_session)
        ) -> TournamentManager:
            return TournamentManager(
                db_session=db_session,
                minio_client=self.minio_client
            )
            
        def get_team_manager(
            db_session: AsyncSession = Depends(self.db_manager.get_session)
        ) -> TeamManager:
            return TeamManager(
                db_session=db_session
            )
            
        def get_user_manager(
            db_session: AsyncSession = Depends(self.db_manager.get_session)
        ) -> UserManager:
            return UserManager(
                db_session=db_session
            )
            
        
        @self.app.get("/")
        def read_root():
            return {"message": "Hello World"}

        @self.app.post("/user/add")
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
        
        @self.app.post("/user/get")
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
                           
        @self.app.post("/user/get_all")
        async def get_users(user_manager: UserManager = Depends(get_user_manager),
                            api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_users")
            try:
                return await user_manager.get_users()
            except Exception as e:
                self.logger.error(f"get_users: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))
            
        @self.app.post("/team/add")
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
            
        @self.app.post("/team/get")
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
            
        @self.app.post("/team/get_all")
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
        
        @self.app.post("/team/remove")
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
            
        @self.app.post("/team/update")
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
            
        @self.app.post("/tournament/add")
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

        @self.app.get("/tournament/get/{tournament_id}")
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
        
        @self.app.post("/tournament/get_all")
        async def get_tournaments(tournament_manager: TournamentManager = Depends(get_tournament_manager),
                                  api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_tournaments")
            try:
                return await tournament_manager.get_tournaments()
            except Exception as e:
                self.logger.error(f"get_tournaments: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))
            
        @self.app.post("/tournament/register_team")
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
                return await tournament_manager.register_team(message)
            except Exception as e:
                self.logger.error(f"register_team: {e}")
                traceback.print_exc()
                return ResponseMessage(success=False, error=str(e))
        

        @self.app.get("/game/get/{game_id}")
        async def get_game(game_id: int, 
                           tournament_manager: TournamentManager = Depends(get_tournament_manager),
                           api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_game: {game_id}")
            res = await tournament_manager.get_game(game_id)
            self.logger.info(f"get_game: {res}")
            return res

        @self.app.get("/game/download_log/{game_id}")
        async def download_log(game_id: str,
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

        @self.app.get("/game/tmp_get_url/{game_id}")
        async def tmp_get_url(game_id: int, 
                              tournament_manager: TournamentManager = Depends(get_tournament_manager),
                              api_key: str = Depends(get_api_key)):
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
        
        @self.app.post("/runner/game_started")
        async def game_started(json: AddGameResponse, 
                               tournament_manager: TournamentManager = Depends(get_tournament_manager),
                               api_key: str = Depends(get_api_key)):
            try:
                self.logger.info(f"game_started: {json}")
                AddGameResponse.validate(json.dict())
                await tournament_manager.handle_game_started(json)
                return {"success": True}
            except Exception as e:
                self.logger.error(f"game_started: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/runner/game_finished")
        async def game_finished(json: GameInfoSummary, 
                                tournament_manager: TournamentManager = Depends(get_tournament_manager),
                                api_key: str = Depends(get_api_key)):
            try:
                self.logger.info(f"game_finished: {json}")
                GameInfoSummary.validate(json.dict())
                await tournament_manager.handle_game_finished(json)
                return {"success": True}
            except Exception as e:
                self.logger.error(f"game_finished: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/runner/register")
        async def register(json: RegisterGameRunnerRequest, 
                           tournament_manager: TournamentManager = Depends(get_tournament_manager),
                           api_key: str = Depends(get_api_key)):
            try:
                self.logger.info(f"register: {json}")
                RegisterGameRunnerRequest.validate(json.dict())
                # return await tournament_manager.register(json)
                return {"success": True}
            except Exception as e:
                self.logger.error(f"register: {e}")
                return {"success": False, "error": str(e)}

    async def run(self):
        self.logger.info('Starting FastAPI app')
        config = uvicorn.Config(self.app, host="0.0.0.0", port=self.port)
        server = uvicorn.Server(config)
        await server.serve()