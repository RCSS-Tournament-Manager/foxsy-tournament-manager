# managers/scheduler.py
import asyncio
from typing import Callable
import logging

class Scheduler:
    def __init__(self, interval: int, function: Callable, *args, **kwargs):
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.task = None
        self.logger = logging.getLogger(__name__)

    async def start(self):
        while True:
            try:
                self.logger.info("Running scheduled function")
                await self.function(*self.args, **self.kwargs)
            except Exception as e:
                # Log the exception
                print(f"Error in scheduled function: {e}")
            await asyncio.sleep(self.interval)

    def run(self):
        self.task = asyncio.create_task(self.start())

    def cancel(self):
        if self.task:
            self.task.cancel()

