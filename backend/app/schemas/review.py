from pydantic import BaseModel, Field
from typing import Optional, List

class ReviewUpsertIn(BaseModel):
    score: Optional[int] = Field(None, ge=0, le=100)  # 0..100
    notes: Optional[str] = Field(None, max_length=4000)
    contains_spoilers: Optional[bool] = False

class ReviewOut(BaseModel):
    user_id: int
    game_id: int
    score: Optional[int]
    notes: Optional[str]
    contains_spoilers: bool
    review_updated_at: Optional[str]
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    likes_count: int = 0
    liked_by_me: bool = False

class GameReviewsResponse(BaseModel):
    game_rawg_id: int
    avg_score_global: Optional[float]
    count_reviews: int
    reviews: List[ReviewOut]
