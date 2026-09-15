"""Типы раундов: название, сложность и очки за правильный ответ."""

ROUND_TYPES = {
    "guess_artist": {"label": "Угадай исполнителя", "difficulty": "просто", "points": 100},
    "guess_track":  {"label": "Угадай название",    "difficulty": "средне", "points": 120},
    "guess_cover":  {"label": "Угадай по обложке",  "difficulty": "средне", "points": 130},
    "by_lyrics":    {"label": "Угадай по тексту",    "difficulty": "средне", "points": 130},
    "speed":        {"label": "Ускоренный трек",     "difficulty": "сложно", "points": 150},
    "ai_fact":      {"label": "Факт от ИИ",          "difficulty": "средне", "points": 140},
}
