from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Tournament(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    start_time: datetime
    commited: bool = False