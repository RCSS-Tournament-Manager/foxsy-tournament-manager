from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


# Define the User class.
class UserModel(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    user_id = Column(Integer)

    def __repr__(self):
        return (f"<UserModel(id={self.id}, name={self.name}, user_id={self.user_id})>")
