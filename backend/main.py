from app.api import friendships
from fastapi import FastAPI, Request
import time
from app.core.init_db import init_db
from app.api import users, user_games, auth, review, users_recommendations, user_friends, games
from app.core.logger_config import get_logger

app = FastAPI(title="PlayTracker API")

# Crear logger principal
logger = get_logger(__name__)

# Middleware para registrar cada petición
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Petición entrante: {request.method} {request.url.path} desde {request.client.host}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception(f"Error procesando {request.method} {request.url.path}: {e}")
        raise

    duration = (time.time() - start_time) * 1000
    logger.info(f"Respuesta: {request.method} {request.url.path} -> {response.status_code} ({duration:.2f} ms)")
    return response

# Eventos de inicio y apagado
@app.on_event("startup")
async def startup():
    logger.info("Iniciando PlayTracker API...")
    await init_db()
    logger.info("Base de datos inicializada correctamente.")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Apagando PlayTracker API...")

# Rutas
app.include_router(users.router)
app.include_router(user_games.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(games.router, prefix="/rawg", tags=["games"])
app.include_router(friendships.router)
app.include_router(review.router)
app.include_router(users_recommendations.router)
app.include_router(user_friends.users_friends_router)

@app.get("/health", status_code=200, tags=["health"])
async def health():
    logger.info("Health check requested")
    return {"status": "ok"}

@app.get("/")
def root():
    logger.info("Ruta raíz accedida")
    return {"message": "PlayTracker API"}