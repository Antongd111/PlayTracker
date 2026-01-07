# app/schemas/friendship.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class UserLite(BaseModel):
    id: int
    username: str
    avatar_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class FriendshipRequestOut(BaseModel):
    friendship_id: int
    requester_id: int
    other_user: UserLite
    status: str
    requested_at: datetime
    model_config = ConfigDict(from_attributes=True)

class FriendOut(UserLite):
    pass
