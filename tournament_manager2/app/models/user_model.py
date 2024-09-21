from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from .base import Base

class UserModel(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    code = Column(String)

    # Relationships
    teams = relationship('TeamModel', back_populates='user', cascade='all, delete-orphan')
    
    # This represents tournaments the user owns
    owned_tournaments = relationship('TournamentModel', back_populates='owner', cascade='all, delete-orphan')

    
    def __repr__(self):
        return f"<UserModel(id={self.id}, name={self.name}, code={self.code})>"