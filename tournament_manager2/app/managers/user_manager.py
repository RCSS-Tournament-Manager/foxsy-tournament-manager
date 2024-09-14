from datetime import datetime
from utils.messages import *
from managers.manager import Manager
from sqlalchemy.orm import joinedload
import asyncio
from sqlalchemy.sql import exists
import logging


class UserManager:
    def __init__(self, manager: Manager):
        self.logger = logging.getLogger(__name__)
        self.logger.info('UserManager created')
        self.manager: Manager = manager

    async def add_user(self, message):
        pass