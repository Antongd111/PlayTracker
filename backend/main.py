from app.api import friendships
from fastapi import FastAPI
from app.core.init_db import init_db
from app.api import users, user_games, auth, review, users_recommendations, user_friends, games

app = FastAPI()

@app.on_event("startup")
async def startup():
    await init_db()

app.include_router(users.router)
app.include_router(user_games.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(games.router, prefix="/rawg", tags=["rawg"])
app.include_router(friendships.router)
app.include_router(review.router)
app.include_router(users_recommendations.router)
app.include_router(user_friends.users_friends_router)

@app.get("/")
def root():
    return {"message": "PlayTracker API"}