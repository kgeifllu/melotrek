import httpx

# работа с текстами песен

LYRICS_URL = "https://api.lyrics.ovh/v1"


def get_lyrics(artist: str, title: str):
    """Возвращает текст песни или None, если его нет."""
    url = f"{LYRICS_URL}/{artist}/{title}"
    try:
        response = httpx.get(url, timeout=10.0)
        if response.status_code != 200:
            return None
        data = response.json()
        lyrics = data.get("lyrics", "").strip()
        return lyrics or None
    except Exception as e:
        print("Ошибка запроса к lyrics.ovh:", e)
        return None


def get_lyrics_lines(artist: str, title: str, n: int = 8):
    """Возвращает первые n непустых строк текста песни или None."""
    lyrics = get_lyrics(artist, title)
    if not lyrics:
        return None
    lines = [ln.strip() for ln in lyrics.split("\n") if ln.strip()]
    if len(lines) < 2:
        return None
    return "\n".join(lines[:n])
