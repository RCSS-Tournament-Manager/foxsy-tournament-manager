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

        @self.app.get("/items/{item_id}")
        def read_item(item_id: int, q: str = None, api_key: str = Depends(get_api_key)):
            return {"item_id": item_id, "q": q}

        @self.app.get("/games")
        def get_games(api_key: str = Depends(get_api_key)):
            return self.manager.get_games()

        @self.app.post("/add_game")
        def add_game(game_info: dict, api_key: str = Depends(get_api_key)):
            if self.manager.available_games_count == 0:
                return None
            game = self.manager.add_game(game_info)
            return game.to_dict()

    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)