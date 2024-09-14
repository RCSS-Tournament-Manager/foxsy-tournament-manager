from datetime import datetime
from utils.messages import *
from managers.database_manager import DataBaseManager
from managers.tournament_manager import TournamentManager
from managers.user_manager import UserManager
from models.message_convertor import MessageConvertor
from sqlalchemy.orm import joinedload
import asyncio
from sqlalchemy.sql import exists
from utils.rmq_message_sender import RmqMessageSender
import logging
from storage.minio_client import MinioClient


class Manager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info('Manager created')
        self.database_manager: DataBaseManager = None
        self.rmq_message_sender: RmqMessageSender = None
        self.minio_client: MinioClient = None
        self.user_manager: UserManager = None
        self.tournament_manager: TournamentManager = None

    async def set_database_manager(self, database_manager: DataBaseManager):
        self.database_manager = database_manager
        
    async def set_rmq_message_sender(self, rmq_message_sender: RmqMessageSender):
        self.rmq_message_sender = rmq_message_sender
        
    async def set_minio_client(self, minio_client: MinioClient):
        self.minio_client = minio_client
    
    async def set_user_manager(self, user_manager: UserManager):
        self.user_manager = user_manager
    
    async def set_tournament_manager(self, tournament_manager: TournamentManager):
        self.tournament_manager = tournament_manager