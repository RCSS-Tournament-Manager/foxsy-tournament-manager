from fastapi import FastAPI, HTTPException, Security, Depends
import uvicorn
from game_runner.runner_manager import RunnerManager
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN
from utils.messages import *
import logging

logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more detailed logs
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
class FastApiApp:
    def __init__(self, manager: RunnerManager, api_key: str, api_key_name: str = "api_key", port: int = 8000):
        self.logger = logging.getLogger(__name__)
        self.app = FastAPI()
        self.manager = manager
        self.api_key = api_key
        self.api_key_name = api_key_name
        self.port = port
        self.setup_routes()
        self.logger.info("Runner FastApiApp initialized")

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

        @self.app.get("/games")
        def get_games(api_key: str = Depends(get_api_key)):
            return self.manager.get_games()

        @self.app.post("/add_game")
        async def add_game(message_json: GameInfoMessage, api_key: str = Depends(get_api_key)):
            try:
                message = message_json
                GameInfoMessage.model_validate(message.model_dump())
                if not message:
                    self.logger.error("game_info is required")
                    raise Exception("game_info is required")
                message.fix_json()
                return await self.manager.add_game(message)
            except Exception as e:
                self.logger.error(f"Error adding game: {str(e)}")
                return {"success": False, "error": str(e)}

        @self.app.post("/stop_game_by_game_id/{game_id}")
        async def stop_game_by_game_id(game_id: int, api_key: str = Depends(get_api_key)):
            return await self.manager.stop_game_by_game_id(game_id)

        @self.app.post("/stop_game_by_port/{port}")
        async def stop_game_by_port(port: int, api_key: str = Depends(get_api_key)):
            return await self.manager.stop_game_by_port(port)
        
        @self.app.post("/runner/receive_command", response_model=ResponseMessage)
        async def receive_command(command_request: RequestedCommandToRunnerMessage, api_key: str = Depends(get_api_key)):
            try:
                command = command_request.command
                self.logger.info(f"Received command: {command}")
                return await self.manager.receive_command(command)
            except Exception as e:
                self.logger.error(f"Error receiving command: {str(e)}")
                return ResponseMessage(success=False, error=str(e))
    
        @self.app.get("/runner/status")
        async def get_runner_status(api_key: str = Depends(get_api_key)):
            return self.manager.status
        
    async def run(self):
        config = uvicorn.Config(self.app, host="0.0.0.0", port=self.port)
        server = uvicorn.Server(config)
        await server.serve()