"""
ИИ-слой через Groq (бесплатный облачный AI).
Ключ — в переменной окружения GROQ_API_KEY.
Используется для: загадок о песне, перевода строки, комментариев ведущего,
итогового поздравления. Если ключа нет / запрос упал — возвращается None,
и игра работает без ИИ-части (не ломается).
"""
import os
import time

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "openai/gpt-oss-20b"


def _ask(system: str, user: str, temperature: float = 0.7):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None
    # до 3 попыток: при 429 (слишком часто) ждём и повторяем
    for attempt in range(3):
        try:
            r = httpx.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": temperature,
                },
                timeout=25.0,
            )
            if r.status_code == 429:
                # превышен лимит частоты — подождать и повторить
                time.sleep(2.0 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print("Groq недоступен:", e)
            time.sleep(1.0)
    return None


def make_fact(artist: str, title: str):
    """Конкретная загадка с уникальными фактами о песне. Для раунда 'Факт от ИИ'."""
    return _ask(
        "Ты ведущий музыкальной викторины. Дай загадку об этой песне на русском "
        "языке из 1-2 предложений, используя КОНКРЕТНЫЕ и УНИКАЛЬНЫЕ факты: год "
        "выхода, необычные детали создания, рекорды, награды, известную строчку "
        "или припев (перефразируй, не цитируй дословно), где песня звучала (фильм, "
        "реклама, мем), коллаборации. НЕ используй общие слова вроде «о любви», "
        "«запоминающийся припев», «яркий вокал» — только конкретику, по которой "
        "реально узнать песню. НЕ называй саму песню и исполнителя. "
        "Если не знаешь точных фактов — назови жанр, эпоху и одну характерную "
        "деталь. Ответь только загадкой.",
        f"Песня: «{title}» — исполнитель: {artist}",
        temperature=0.6)


def translate_line(line: str):
    """Перевод строки песни на русский. Для раунда 'Перевод строки'."""
    return _ask(
        "Переведи строку песни на русский язык дословно. "
        "Ответь только переводом, без пояснений.", line)


def comment_answer(team: str, correct: bool, answer: str, right: str):
    """Живой комментарий ведущего на ответ команды."""
    if correct:
        user = f"Команда «{team}» ответила верно: {right}. Похвали кратко и весело."
    else:
        user = (f"Команда «{team}» ответила неверно («{answer}»), правильный ответ "
                f"был «{right}». Подбодри кратко и по-доброму.")
    return _ask(
        "Ты весёлый ведущий музыкальной викторины. Отвечай ОДНОЙ короткой фразой "
        "на русском, с лёгким юмором, без грубости.", user, temperature=0.9)


def final_words(standings: list):
    """Итоговое поздравление по таблице лидеров. standings: [(team, score), ...]."""
    table = "; ".join(f"{t}: {s}" for t, s in standings)
    return _ask(
        "Ты ведущий музыкальной викторины. По итоговой таблице напиши весёлое "
        "поздравление победителю и доброе слово остальным. 2-3 предложения на русском.",
        f"Итоги: {table}", temperature=0.9)


# совместимость (старый раунд перефразирования, не используется в игре)
def make_paraphrase(text: str):
    r = _ask("Перефразируй строку песни другими словами, сохранив смысл. "
             "Ответь только перефразированной строкой.", text)
    return (r, "ai") if r else (text, "fallback")
