from fastapi import FastAPI, HTTPException, Security, Depends
import uvicorn
from managers.manager import Manager
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from utils.messages import *
import logging
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

class FastApiApp:
    def __init__(self, manager: Manager, api_key: str, api_key_name: str = "api_key", port: int = 8000):
        self.logger = logging.getLogger(__name__)
        self.app = FastAPI()
        self.manager:Manager = manager
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
        @self.app.get("/")
        def read_root():
            return {"message": "Hello World"}

        @self.app.post("/user/add")
        async def add_user(name:str, id: str, api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.post("/user/delete")
        async def delete_user(id: str, api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.post("/team/add")
        async def add_team(message_json: AddTeamRequestMessage, api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.post("/team/update_config")
        async def update_team_config(message_json: UpdateTeamConfigRequestMessage, api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.post("/tournament/add")
        async def add_tournament(message_json: AddTournamentRequestMessage, api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.post("/tournament/add_team")
        async def add_team_to_tournament(message_json: AddTeamToTournamentRequestMessage, api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.post("/tournament/remove_team")
        async def remove_team_from_tournament(message_json: RemoveTeamFromTournamentRequestMessage, api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.get("/tournament/get_all")
        async def get_all_tournaments(api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.get("/tournament/get_all_ids")
        async def get_all_tournament_ids(api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.get("/tournament/get/{id}")
        async def get_tournament(id: int, api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.get("/tournament/get_teams/{id}")
        async def get_tournament_teams(id: int, api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.get("/tournament/get_games/{id}")
        async def get_tournament_games(id: int, api_key: str = Depends(get_api_key)):
            pass
        
        @self.app.get("/game/get/{id}")
        async def get_game(id: int, api_key: str = Depends(get_api_key)):
            pass
        
        
        @self.app.post("/add_tournament")
        async def add_tournament(message_json: AddTournamentRequestMessage, api_key: str = Depends(get_api_key)):
            self.logger.info(f"add_tournament: {message_json}")
            try:
                message = message_json
                AddTournamentRequestMessage.validate(message.dict())
                if not message.teams:
                    raise Exception("teams is required")
                for team in message.teams:
                    TeamMessage.validate(team)
                    team.fix_json()
                self.logger.info(f"add_tournament: adding message to tournament manager: {message}")
                return await self.manager.tournament_manager.add_tournament(message)
            except Exception as e:
                self.logger.error(f"add_tournament: {e}")
                return AddTournamentResponseMessage(tournament_id=None, success=False, error=str(e))

        @self.app.get("/get_tournament/{tournament_id}")
        async def get_tournament(tournament_id: int, api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_tournament: {tournament_id}")
            res = await self.manager.tournament_manager.get_tournament(tournament_id)
            self.logger.info(f"get_tournament: {res}")
            return res

        @self.app.get("/get_game/{game_id}")
        async def get_game(game_id: int, api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_game: {game_id}")
            res = await self.manager.tournament_manager.get_game(game_id)
            self.logger.info(f"get_game: {res}")
            return res

        @self.app.get("/download_log/{game_id}")
        async def download_log(game_id: str):
            self.logger.info(f"download_log: {game_id}")
            game_log_name = f"{game_id}.zip"
            tmp_file_path = os.path.join("/tmp", game_log_name)
            try:
                res = await self.manager.tournament_manager.download_log_file(game_id, tmp_file_path)
                if not res:
                    raise Exception(f"File not found: {game_id}")
                if not os.path.exists(tmp_file_path):
                    raise Exception(f"File not found: {tmp_file_path}")
                return FileResponse(tmp_file_path, media_type="application/octet-stream", filename=game_log_name)
            except Exception as e:
                raise HTTPException(status_code=404, detail=f"File not found or {e}") from e

        @self.app.get("/get_tournaments")
        async def get_tournaments(api_key: str = Depends(get_api_key)):
            self.logger.info(f"get_tournaments")
            res = await self.manager.tournament_manager.get_tournaments()
            self.logger.info(f"get_tournaments: {res}")
            return res

        @self.app.post("/game_started")
        async def game_started(json: AddGameResponse, api_key: str = Depends(get_api_key)):
            try:
                self.logger.info(f"game_started: {json}")
                AddGameResponse.validate(json.dict())
                await self.manager.tournament_manager.handle_game_started(json)
                return {"success": True}
            except Exception as e:
                self.logger.error(f"game_started: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/game_finished")
        async def game_finished(json: GameInfoSummary, api_key: str = Depends(get_api_key)):
            try:
                self.logger.info(f"game_finished: {json}")
                GameInfoSummary.validate(json.dict())
                await self.manager.tournament_manager.handle_game_finished(json)
                return {"success": True}
            except Exception as e:
                self.logger.error(f"game_finished: {e}")
                return {"success": False, "error": str(e)}

        @self.app.post("/register")
        async def register(json: RegisterGameRunnerRequest, api_key: str = Depends(get_api_key)):
            try:
                self.logger.info(f"register: {json}")
                RegisterGameRunnerRequest.validate(json.dict())
                # return await self.manager.register(json)
                return {"success": True}
            except Exception as e:
                self.logger.error(f"register: {e}")
                return {"success": False, "error": str(e)}

        @self.app.get("/tmp_get_url/{game_id}")
        async def tmp_get_url(game_id: int, api_key: str = Depends(get_api_key)):
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
                    res = await self.manager.tournament_manager.download_log_file(game_id, tmp_file_path)
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

    async def run(self):
        self.logger.info('Starting FastAPI app')
        config = uvicorn.Config(self.app, host="0.0.0.0", port=self.port)
        server = uvicorn.Server(config)
        await server.serve()