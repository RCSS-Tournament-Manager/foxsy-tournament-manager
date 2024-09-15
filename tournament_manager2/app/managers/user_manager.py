from datetime import datetime
from utils.messages import *
from models.user_model import UserModel
from models.message_convertor import MessageConvertor
from sqlalchemy.orm import selectinload
from sqlalchemy import select, exists, and_
import asyncio
import logging
from typing import AsyncGenerator, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

class UserManager:
    def __init__(self, db_session: AsyncSession):
        self.logger = logging.getLogger(__name__)
        self.logger.info('UserManager created')
        self.db_session = db_session
        
    async def add_user(self, message: AddUserRequestMessage) -> ResponseMessage:
        """
        Adds a new user to the database if the user_name and user_code are unique.
        """
        self.logger.info(f"Attempting to add user with name: '{message.user_name}' and code: '{message.user_code}'")
        session = self.db_session

        # Check if user_name is unique
        stmt_name = select(UserModel).where(UserModel.name == message.user_name)
        result_name = await session.execute(stmt_name)
        existing_user_by_name = result_name.scalars().first()
        if existing_user_by_name:
            self.logger.error(f"User with name '{message.user_name}' already exists")
            return ResponseMessage(success=False, error=f"User with name '{message.user_name}' already exists")

        # Check if user_code is unique
        stmt_code = select(UserModel).where(UserModel.code == message.user_code)
        result_code = await session.execute(stmt_code)
        existing_user_by_code = result_code.scalars().first()
        if existing_user_by_code:
            self.logger.error(f"User with code '{message.user_code}' already exists")
            return ResponseMessage(success=False, error=f"User with code '{message.user_code}' already exists")

        # Create new user
        new_user = UserModel(name=message.user_name, code=message.user_code)
        session.add(new_user)
        try:
            await session.commit()
            await session.refresh(new_user)
            self.logger.info(f"User added with id: {new_user.id}")
            return ResponseMessage(success=True, message="User added successfully")
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Error adding user: {e}")
            return ResponseMessage(success=False, error="An error occurred while adding the user")
        
    async def get_user_or_create(self, user_code: str) -> Optional[UserModel]:
        """
        Retrieves the user model on the user_code.
        If the user does not exist, creates a new user with a default name.
        """
        self.logger.info(f"Retrieving user id for user_code: '{user_code}'")
        session = self.db_session

        # Find user based on the code
        stmt = select(UserModel).where(UserModel.code == user_code)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user:
            self.logger.info(f"Found existing user with id: {user.id}")
            return user
        else:
            # Create the user if not exist
            self.logger.info(f"No user found with code '{user_code}', creating new user")
            default_user_name = f"user_{user_code}"
            new_user = UserModel(name=default_user_name, code=user_code)
            session.add(new_user)
            try:
                await session.commit()
                await session.refresh(new_user)
                self.logger.info(f"New user created with id: {new_user.id}")
                return new_user
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Error creating user: {e}")
                raise e  # Raise exception or handle it appropriately
            
    async def get_user(self, message: GetUserRequestMessage) -> Optional[UserModel]:
        """
        Retrieves the user based on the provided criteria.
        """
        self.logger.info(f"Retrieving user with code: '{message.user_code}', id: '{message.user_id}', name: '{message.user_name}'")
        session = self.db_session

        # Find user based on the provided criteria
        stmt = select(UserModel)
        if message.user_code:
            stmt = stmt.where(UserModel.code == message.user_code)
        if message.user_id:
            stmt = stmt.where(UserModel.id == message.user_id)
        if message.user_name:
            stmt = stmt.where(UserModel.name == message.user_name)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if user:
            self.logger.info(f"Found user with id: {user.id}")
            return user
        else:
            self.logger.error("No user found")
            return None
        
    async def get_user_info(self, message: GetUserRequestMessage) -> GetUserResponseMessage:
        """
        Retrieves the user information based on the provided criteria.
        """
        self.logger.info(f"Retrieving user info with code: '{message.user_code}', id: '{message.user_id}', name: '{message.user_name}'")
        session = self.db_session

        # Find user based on the provided criteria
        stmt = select(UserModel).options(
            selectinload(UserModel.owned_tournaments),
            selectinload(UserModel.participating_tournaments),
            selectinload(UserModel.teams)
        )
        if message.user_code:
            stmt = stmt.where(UserModel.code == message.user_code)
        if message.user_id:
            stmt = stmt.where(UserModel.id == message.user_id)
        if message.user_name:
            stmt = stmt.where(UserModel.name == message.user_name)
        
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            self.logger.error("No user found")
            raise Exception("User not found")
        
        # TODO: Fix bug here
        # Get the list of owned tournaments
        owned_tournament_ids = []
        for tournament in user.owned_tournaments:
            owned_tournament_ids.append(tournament.id)

        # # Get the list of tournaments the user is in
        in_tournament_ids = []
        for tournament in user.participating_tournaments:
            in_tournament_ids.append(tournament.id)
        
        # Get the list of teams the user owns
        team_ids = []
        for team in user.teams:
            team_ids.append(team.id)
        
        user_message = GetUserResponseMessage(
            user_id=user.id,
            user_name=user.name,
            owned_tournament_ids=owned_tournament_ids,
            in_tournament_ids=in_tournament_ids,
            team_ids=team_ids
        )
        
        self.logger.info(f"User info retrieved: {user_message}")
        return user_message
    
    async def get_users(self) -> GetUsersResponseMessage:
        """
        Retrieves all the users in the database.
        """
        self.logger.info(f"Retrieving all users")
        session = self.db_session

        stmt = select(UserModel)
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        user_messages = []
        for user in users:
            user_message = GetUserResponseMessage(
                user_id=user.id,
                user_name=user.name
            )
            user_messages.append(user_message)
        
        self.logger.info(f"Users retrieved: {user_messages}")
        return GetUsersResponseMessage(users=user_messages)
    
