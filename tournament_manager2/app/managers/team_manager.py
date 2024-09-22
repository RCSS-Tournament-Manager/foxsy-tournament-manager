from datetime import datetime
from utils.messages import *
from models.tournament_model import TournamentModel
from models.team_model import TeamModel
from models.user_model import UserModel
from models.game_model import GameModel, GameStatusEnum
from models.message_convertor import MessageConvertor
from sqlalchemy.orm import selectinload
from sqlalchemy import select, exists, and_
import asyncio
import logging
from storage.minio_client import MinioClient
from typing import AsyncGenerator, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError


class TeamManager:
    def __init__(self, db_session: AsyncSession):
        self.logger = logging.getLogger(__name__)
        self.logger.info('TeamManager created')
        self.db_session = db_session
        
    async def create_team(self, message: AddTeamRequestMessage) -> Union[GetTeamResponseMessage, ResponseMessage]:
        """
        Create a team with a unique name for the user. If the team name already exists, 
        find a unique name by appending '_n' where 'n' is an incrementing integer.
        """
        self.logger.info(f"Creating team: {message.team_name} for user with code: {message.user_code}")
        session = self.db_session
        
        stmt = select(UserModel).filter_by(code=message.user_code)
        user = await session.execute(stmt)
        user = user.scalars().first()
        if user is None:
            self.logger.error(f"User not found.") # TODO Add Test
            return GetTeamResponseMessage(success=False, error="User not found")

        user_id = user.id
        
        # Check if the team name is unique
        base_name = message.team_name
        team_name = base_name
        i = 1
        while True:
            stmt = select(TeamModel).filter_by(name=team_name)
            result = await session.execute(stmt)
            existing_team = result.scalars().first()
            if not existing_team:
                break
            team_name = f"{base_name}_{i}"
            i += 1
        
        # Create a new team
        new_team = TeamModel(name=team_name, user_id=user_id, base_team=base_name, config="{}")
        session.add(new_team)
        await session.commit()
        await session.refresh(new_team)
        
        self.logger.info(f"Team created with id: {new_team.id}, name: {new_team.name}")
        
        response = await self.get_team(GetTeamRequestMessage(user_code=message.user_code, team_id=new_team.id))
        return response

    async def get_team(self, message: GetTeamRequestMessage) -> Union[GetTeamResponseMessage, ResponseMessage]:
        """
        Retrieve a team if the user is the owner.
        """
        self.logger.info(f"Getting team with id: {message.team_id} for user with: {message.user_code}")
        session = self.db_session
        
        user_id = None
        if message.user_code is not None:
            stmt = select(UserModel).filter_by(code=message.user_code)
            user = await session.execute(stmt)
            user = user.scalars().first()
            if user is not None:
                user_id = user.id
        
        stmt = select(TeamModel)
        if message.team_id is not None:
            stmt = stmt.filter_by(id=message.team_id)
        if message.team_name is not None:
            stmt = stmt.filter_by(name=message.team_name)
            
        result = await session.execute(stmt)
        team = result.scalars().first()

        if not team:
            self.logger.error(f"Team not found or user does not own the team.")
            return ResponseMessage(success=False, error="Team not found")

        team_message = GetTeamResponseMessage(
            user_code=message.user_code,
            team_id=team.id,
            team_name=team.name,
            base_team_name=team.base_team,
            team_config_json=team.config if user_id == team.user_id else None
        )

        self.logger.info(f"Team retrieved: {team_message}")
        return team_message

    async def remove_team(self, message: RemoveTeamRequestMessage) -> ResponseMessage:
        """
        Remove a team if the user is the owner, the team is not in any tournament or game.
        """
        self.logger.info(f"Removing team with id: {message.team_id} for user with code: {message.user_code}")
        session = self.db_session

        stmt = select(UserModel).filter_by(code=message.user_code)
        user = await session.execute(stmt)
        user = user.scalars().first()
        user_id = user.id
        
        # Ensure the user owns the team
        stmt = select(TeamModel).filter_by(id=message.team_id, user_id=user_id)
        result = await session.execute(stmt)
        team = result.scalars().first()

        if not team:
            self.logger.error(f"Team not found or user does not own the team.")
            return ResponseMessage(success=False, error="Team not found or user does not own the team")

        # Ensure the team is not in any tournaments
        stmt_tournament = select(TournamentModel).filter(TournamentModel.teams.contains(team))
        result_tournament = await session.execute(stmt_tournament)
        tournament = result_tournament.scalars().first()

        if tournament:
            self.logger.error(f"Team is in an ongoing tournament and cannot be deleted.")
            return ResponseMessage(success=False, error="Team is in an ongoing tournament and cannot be deleted.")

        # Ensure the team is not part of any games
        stmt_game = select(GameModel).filter(
            (GameModel.left_team_id == team.id) | (GameModel.right_team_id == team.id)
        )
        result_game = await session.execute(stmt_game)
        game = result_game.scalars().first()

        if game:
            self.logger.error(f"Team is involved in a game and cannot be deleted.")
            return ResponseMessage(success=False, error="Team is involved in a game and cannot be deleted.")

        # Remove the team
        await session.delete(team)
        await session.commit()
        self.logger.info(f"Team with id {team.id} removed successfully.")
        return ResponseMessage(success=True)

    async def update_team(self, message: UpdateTeamRequestMessage) -> Union[GetTeamResponseMessage, ResponseMessage]:
        """
        Update a team's base_team_name and team_config_json if the user is the owner.
        """
        try:
            self.logger.info(f"Updating team with id: {message.team_id} for user with code: {message.user_code}")
            session = self.db_session

            stmt = select(UserModel).filter_by(code=message.user_code)
            user = await session.execute(stmt)
            user = user.scalars().first()
            if user is None:
                self.logger.error(f"User not found.")
                return ResponseMessage(success=False, error="User not found")
            user_id = user.id
            
            # Ensure the user owns the team
            stmt = select(TeamModel).filter_by(id=message.team_id, user_id=user_id)
            result = await session.execute(stmt)
            team = result.scalars().first()

            if not team:
                self.logger.error(f"Team not found or user does not own the team.")
                return ResponseMessage(success=False, error="Team not found or user does not own the team")

            # Update the team's base_team_name and team_config_json
            if message.base_team_name is not None:
                team.base_team = message.base_team_name
            if message.team_config_json is not None:
                team.config = message.team_config_json
            await session.commit()
            await session.refresh(team)
            
            team_message = GetTeamResponseMessage(
                user_code=message.user_code,
                team_id=team.id,
                team_name=team.name,
                base_team_name=team.base_team,
                team_config_json=team.config
            )

            self.logger.info(f"Team updated: {team_message}")
            return team_message
        except SQLAlchemyError as e:
            return None
        except Exception as e:
            return None

    async def get_teams(self) -> GetTeamsResponseMessage:
        """
        Retrieve all teams.
        """
        self.logger.info(f"Getting all teams")
        session = self.db_session

        stmt = select(TeamModel)
        result = await session.execute(stmt)
        teams = result.scalars().all()

        team_messages = []
        for team in teams:
            team_message = TeamMessage(
                team_id=team.id,
                team_name=team.name,
                base_team_name=team.base_team,
                user_id=team.user_id
            )
            team_messages.append(team_message)

        response = GetTeamsResponseMessage(teams=team_messages)
        self.logger.info(f"Teams retrieved: {response}")
        return response