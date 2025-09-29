from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    status = Column(String, default="Disponible")
    avatar_url = Column(String)
    favorite_rawg_game_id = Column(BigInteger, nullable=True)
    
    games = relationship("UserGame", back_populates="user")