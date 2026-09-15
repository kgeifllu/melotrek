import httpx
from sqlalchemy.orm import Session

from app.models import Track

# работа с iTunes (музыка)

ITUNES_URL = "https://itunes.apple.com/search"


def search_tracks(query: str, limit: int = 25):
    """Ищет ТОЛЬКО отдельные песни в iTunes (не сборники/плейлисты/подкасты).
    Отбрасывает всё без превью, без исполнителя или без названия."""
    params = {
        "term": query,
        "media": "music",
        "entity": "song",     # только песни, не альбомы и не сборники
        "limit": limit,
    }
    try:
        response = httpx.get(ITUNES_URL, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print("Ошибка запроса к iTunes:", e)
        return []

    tracks = []
    for item in data.get("results", []):
        # берём только настоящие песни
        if item.get("wrapperType") != "track":
            continue
        if item.get("kind") != "song":
            continue
        if not item.get("previewUrl"):
            continue
        title = (item.get("trackName") or "").strip()
        artist = (item.get("artistName") or "").strip()
        if not title or not artist:
            continue
        tracks.append({
            "external_id": str(item.get("trackId")),
            "title": title,
            "artist": artist,
            "preview_url": item.get("previewUrl"),
            "artwork_url": item.get("artworkUrl100"),
            "year": (item.get("releaseDate") or "")[:4],
            "genre": item.get("primaryGenreName", ""),
        })
    return tracks


def save_tracks(db: Session, tracks: list):
    """Сохраняет треки в базу без дублей (кэш)."""
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
