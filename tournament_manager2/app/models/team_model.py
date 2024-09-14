from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


# Define the Team class.
class TeamModel(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    base_team = Column(String)
    config = Column(String)

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('UserModel', back_populates='teams')
    
    def __repr__(self):
        return (f"<TeamModel(id={self.id}, name={self.name}, user_id={self.user_id}, base_team={self.base_team}, "
                f"config={self.config})>")
