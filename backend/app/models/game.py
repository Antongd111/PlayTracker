from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from sqlalchemy import Integer, String, Date, Float, Text, JSON, DateTime, func, UniqueConstraint
from app.core.database import Base

class Game(Base):
    __tablename__ = "games"
    __table_args__ = (
        UniqueConstraint("rawg_id", name="uq_games_rawg_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rawg_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Campos principales
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    release_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Listas
    platforms: Mapped[list[str]] = mapped_column(JSON, default=list)
    genres: Mapped[list[str]] = mapped_column(JSON, default=list)
    developers: Mapped[list[str]] = mapped_column(JSON, default=list)
    publishers: Mapped[list[str]] = mapped_column(JSON, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    screenshots: Mapped[list[str]] = mapped_column(JSON, default=list)
    videos: Mapped[list[str]] = mapped_column(JSON, default=list)
    similar_games: Mapped[list[dict]] = mapped_column(JSON, default=list)

    # Otros metadatos
    esrb_rating: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metacritic_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metacritic_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())