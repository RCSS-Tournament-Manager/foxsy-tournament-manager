from datetime import datetime
import logging
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, select

from model.game import Game, GameStatus
from model.game_result import GameResult
from model.team import Team
from model.tournament import Tournament


class TournamentManager:
    def __init__(self):
        self.db = create_engine('sqlite:///../storage/data/tournament.db', connect_args={"check_same_thread": False})
        SQLModel.metadata.create_all(self.db)
        self.logging = logging.getLogger("TournamentManager")
        
    def create_tournament(self, tournament: Tournament) -> Tournament:
        with Session(self.db) as session:
            session.add(tournament)
            session.commit()
            session.refresh(tournament)
        return tournament
        
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
    
    def add_team_to_tournament(self, tournament_id: int, team: Team) -> Team:
        with Session(self.db) as session:
            team.tournament_id = tournament_id
            session.add(team)
            session.commit()
            session.refresh(team)
        return team
    
    def add_teams_to_tournament(self, tournament_id: int, teams: list[Team]) -> list[Team]:
        with Session(self.db) as session:
            for team in teams:
                team.tournament_id = tournament_id
                session.add(team)
            session.commit()
            for team in teams:
                session.refresh(team)
        return teams
    
    def commit_tournament(self, tournament_id: int) -> Tournament:
        with Session(self.db) as session:
            statement = select(Tournament).where(Tournament.id == tournament_id)
            tournament = session.exec(statement).first()
            tournament.commited = True
            session.add(tournament)
            
            statement = select(Team).where(Team.tournament_id == tournament_id)
            teams = session.exec(statement).all()
            
            # make games
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
            session.refresh(tournament)
        return tournament
    
    def edit_tournament(self, tournament_id: int, tournament: Tournament) -> Tournament:
        with Session(self.db) as session:
            statement = select(Tournament).where(Tournament.id == tournament_id)
            old_tournament = session.exec(statement).first()
            if old_tournament.commited == True:
                self.logging.error("Tournament is commited, cannot edit. Uncommit it first. (The games will be removed if you uncommit it)")
                return None
            
            old_tournament.name = tournament.name
            old_tournament.start_time = tournament.start_time
            session.add(old_tournament)
            session.commit()
            session.refresh(old_tournament)
        return old_tournament
    
    def uncommit_tournament(self, tournament_id: int) -> Tournament:
        with Session(self.db) as session:
            statement = select(Tournament).where(Tournament.id == tournament_id)
            tournament = session.exec(statement).first()
            tournament.commited = False
            session.add(tournament)
            
            statement = select(Game).where(Game.tournament_id == tournament_id)
            games = session.exec(statement).all()
            for game in games:
                session.delete(game)
            session.commit()
            session.refresh(tournament)
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