import httpx
from sqlalchemy.orm import Session

from app.models import Track

ITUNES_URL = "https://itunes.apple.com/search"


def search_tracks(query: str, limit: int = 10):
    """Ищет треки в iTunes. Возвращает список словарей.
    Треки без превью отбрасываются — они бесполезны для квиза."""
    params = {"term": query, "media": "music", "limit": limit}
    try:
        response = httpx.get(ITUNES_URL, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("Ошибка запроса к iTunes:", e)
        return []

    tracks = []
    for item in data.get("results", []):
        if not item.get("previewUrl"):
            continue  # нет превью — пропускаем
        tracks.append({
            "external_id": str(item.get("trackId")),
            "title": item.get("trackName", ""),
            "artist": item.get("artistName", ""),
            "preview_url": item.get("previewUrl"),
            "artwork_url": item.get("artworkUrl100"),
            "year": (item.get("releaseDate") or "")[:4],
            "genre": item.get("primaryGenreName", ""),
        })
    return tracks


def save_tracks(db: Session, tracks: list):
    """Сохраняет треки в базу. Дубли (по external_id) не создаёт — это кэш."""
    saved = []
    for t in tracks:
        existing = db.query(Track).filter(Track.external_id == t["external_id"]).first()
        if existing:
            saved.append(existing)
            continue
        track = Track(**t)
        db.add(track)
        db.commit()
        db.refresh(track)
        saved.append(track)
    return saved
