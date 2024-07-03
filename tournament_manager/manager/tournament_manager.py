from datetime import datetime
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, select

from model.game import Game, GameStatus
from model.game_result import GameResult
from model.team import Team
from model.tournament import Tournament


class TournamentManager:
    def __init__(self):
        self.db = create_engine('sqlite:///../storage/data/tournament.db')
        SQLModel.metadata.create_all(self.db)
        
    def create_tournament(self,
                          tournament_name: str,
                          start_time: datetime,
                          teams: list[Team]) -> Tournament:
        tournament = Tournament(name=tournament_name, start_time=start_time)
        
        # making tournament
        with Session(self.db) as session:
            session.add(tournament)
            session.commit()
            session.refresh(tournament)
        
        # making teams
        with Session(self.db) as session:
            for team in teams:
                team.tournament_id = tournament.id
                session.add(team)
            session.commit()
            for team in teams:
                session.refresh(team)
        
        # making games
        with Session(self.db) as session:
            for i in range(len(teams)):
                for j in range(i + 1, len(teams)):
                    team_left = teams[i]
                    team_right = teams[j]
                    session.add(Game(tournament_id=tournament.id,
                                     team_left_id=team_left.id,
                                     team_right_id=team_right.id,
                                     start_time=None,
                                     end_time=None,
                                     status=GameStatus.WAITING,
                                     order=0))
            session.commit()
        
        return tournament
    
    def change_game_order(self, game_id: int, order: int):
        with Session(self.db) as session:
            statement = select(Game).where(Game.id == game_id)
            game = session.exec(statement).first()
            game.order = order
            session.add(game)
            session.commit()

    def get_tournaments_that_should_start(self) -> list[Tournament]:
        with Session(self.db) as session:
            statement = select(Tournament).where(Tournament.start_time <= datetime.now())
            return session.exec(statement).all()
    
    def run_tournament(self, tournament: Tournament):
        with Session(self.db) as session:
            statement = select(Game).where(Game.tournament_id == tournament.id)
            games = session.exec(statement).all()
            for game in games:
                game.status = GameStatus.PENDING
                session.add(game)
            session.commit()
    
    def game_started(self, game_id: int):
        with Session(self.db) as session:
            statement = select(Game).where(Game.id == game_id)
            game = session.exec(statement).first()
            game.status = GameStatus.IN_PROGRESS
            game.start_time = datetime.now()
            session.add(game)
            session.commit()
    
    def game_finished(self, game_id: int, winner_id: int, team_left_score: int, team_right_score: int):
        with Session(self.db) as session:
            statement = select(Game).where(Game.id == game_id)
            game = session.exec(statement).first()
            game.status = GameStatus.FINISHED
            game.end_time = datetime.now()
            game_result = GameResult(game_id=game_id,
                                     team_left_score=team_left_score,
                                     team_right_score=team_right_score,
                                     winner_id=winner_id)
            session.add(game)
            session.add(game_result)
            session.commit()