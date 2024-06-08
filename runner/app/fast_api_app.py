from fastapi import FastAPI
import uvicorn
from game_runner.manager import Manager


class FastApiApp:
    def __init__(self, manager: Manager):
        self.app = FastAPI()
        self.setup_routes()
        self.manager = manager

    def setup_routes(self):
        @self.app.get("/")
        def read_root():
            return {"message": "Hello World"}

        @self.app.get("/items/{item_id}")
        def read_item(item_id: int, q: str = None):
            return {"item_id": item_id, "q": q}

        @self.app.get("/games")
        def get_games():
            return self.manager.get_games()

        @self.app.post("/add_game")
        def add_game(game_info: dict):
            if self.manager.available_games_count == 0:
                return None
            game = self.manager.add_game(game_info)
            return game.to_dict()

    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=8000)