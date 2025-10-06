from sqlalchemy.orm import Session
from ..models.game_catalog import GameCatalog

def upsert_game_catalog(db: Session, *, rawg_id: int, name: str,
                        genres: list[str] | None, tags: list[str] | None,
                        platforms: list[str] | None,
                        metacritic: int | None = None,
                        rating: float | None = None) -> GameCatalog:
    g = db.get(GameCatalog, rawg_id)
    genres_str = ";".join(genres or [])
    tags_str = ";".join(tags or [])
    plats_str = ";".join(platforms or [])
    if g is None:
        g = GameCatalog(
            game_rawg_id=rawg_id, name=name,
            genres=genres_str, tags=tags_str, platforms=plats_str,
            metacritic=metacritic, rating=rating
        )
        db.add(g)
    else:
        g.name = name
        g.genres = genres_str
        g.tags = tags_str
        g.platforms = plats_str
        g.metacritic = metacritic
        g.rating = rating
    db.commit()
    db.refresh(g)
    return g

def get_popular_games(db: Session, limit: int = 20) -> list[int]:
    q = db.query(GameCatalog).order_by(
        GameCatalog.metacritic.desc().nullslast(),
        GameCatalog.rating.desc().nullslast()
    ).limit(limit)
    return [g.game_rawg_id for g in q.all()]
