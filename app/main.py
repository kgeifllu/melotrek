from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.services.music_api import search_tracks, save_tracks

# создаём все таблицы при запуске
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Мелотрек")
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/tracks/search")
def tracks_search(query: str, db: Session = Depends(get_db)):
    """Ищет треки во внешнем API и сохраняет их в базу (кэш)."""
    found = search_tracks(query)
    saved = save_tracks(db, found)
    return [
        {"id": t.id, "title": t.title, "artist": t.artist,
         "preview_url": t.preview_url}
        for t in saved
    ]
