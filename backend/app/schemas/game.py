from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class SimilarGame(BaseModel):
    id: int
    title: str
    imageUrl: str

class GameDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    title: str
    description: str
    releaseDate: Optional[date] = Field(default=None, validation_alias="release_date")
    imageUrl: Optional[str] = Field(default=None, validation_alias="image_url")
    rating: float = 0.0
    platforms: List[str] = []
    genres: List[str] = []
    developers: List[str] = []
    publishers: List[str] = []
    tags: List[str] = []
    esrbRating: Optional[str] = None
    metacriticScore: Optional[int] = None
    metacriticUrl: Optional[str] = None
    website: Optional[str] = None
    screenshots: List[str] = []
    videos: List[str] = []
    similarGames: List[dict] = []

class GamePreview(BaseModel):
    id: int
    title: str
    imageUrl:str
    year: int

class Recommendations(BaseModel):
    user_id: int
    items: List[GamePreview]