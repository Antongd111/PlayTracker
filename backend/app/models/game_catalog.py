from sqlalchemy import Column, BigInteger, Integer, String, Float
from sqlalchemy.orm import relationship
from ..core.database import Base

class GameCatalog(Base):
    __tablename__ = "game_catalog"

    game_rawg_id = Column(BigInteger, primary_key=True, index=True)
    name = Column(String, nullable=False)

    # listas serializadas por ';'
    genres = Column(String, nullable=True)
    tags = Column(String, nullable=True)
    platforms = Column(String, nullable=True)

    metacritic = Column(Integer, nullable=True)
    rating = Column(Float, nullable=True)
