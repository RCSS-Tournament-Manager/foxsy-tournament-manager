from fastapi import FastAPI, HTTPException, Security, Depends
import uvicorn
from game_runner.manager import Manager
from fastapi.security.api_key import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN


class FastApiApp:
    def __init__(self, manager: Manager, api_key: str, api_key_name: str = "api_key", port: int = 8000):
        self.app = FastAPI()
        self.manager = manager
        self.api_key = api_key
        self.api_key_name = api_key_name
        self.port = port
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

        @self.app.get("/games")
        def get_games(api_key: str = Depends(get_api_key)):
            return self.manager.get_games()

        @self.app.post("/add_game")
        async def add_game(game_info: dict, api_key: str = Depends(get_api_key)):
            if self.manager.available_games_count == 0:
                return None
            game = await self.manager.add_game(game_info)
            return game.to_dict()

        @self.app.post("/stop_game_by_game_id/{game_id}")
        async def stop_game_by_game_id(game_id: int, api_key: str = Depends(get_api_key)):
            return await self.manager.stop_game_by_game_id(game_id)

        @self.app.post("/stop_game_by_port/{port}")
        async def stop_game_by_port(port: int, api_key: str = Depends(get_api_key)):
            return await self.manager.stop_game_by_port(port)

    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)