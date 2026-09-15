from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import Base, engine, get_db
from app import models, schemas
from app.services.music_api import search_tracks, save_tracks
from app.services.lyrics_api import get_lyrics, get_lyrics_lines
from app.services.ai_service import make_paraphrase, make_fact, comment_answer, final_words
from app.services.rounds import check_answer, check_artists, calculate_points
from app.services.genres import GENRE_QUERIES, GENRE_LABELS
from app.services.round_types import ROUND_TYPES

#сердце: все маршруты (эндпоинты) 

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Мелотрек")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ---------- СТРАНИЦЫ ----------

@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/play/{game_id}")
def play_page(request: Request, game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Игра не найдена")
    return templates.TemplateResponse(request, "play.html", {"game": game})


@app.get("/leaderboard/{game_id}")
def leaderboard_page(request: Request, game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Игра не найдена")
    rows = _leaderboard_rows(db, game_id)
    return templates.TemplateResponse(
        request, "leaderboard.html", {"game": game, "rows": rows}
    )


def _leaderboard_rows(db, game_id):
    return (
        db.query(models.Team.name,
                 func.coalesce(func.sum(models.Answer.points), 0).label("score"))
        .outerjoin(models.Answer, models.Answer.team_id == models.Team.id)
        .filter(models.Team.game_id == game_id)
        .group_by(models.Team.id)
        .order_by(func.sum(models.Answer.points).desc())
        .all()
    )


# ---------- CRUD: ИГРЫ ----------

@app.post("/games")
def create_game(data: schemas.GameCreate, db: Session = Depends(get_db)):
    game = models.Game(title=data.title)
    db.add(game); db.commit(); db.refresh(game)
    return {"id": game.id, "title": game.title, "status": game.status}


@app.get("/games")
def list_games(db: Session = Depends(get_db)):
    return db.query(models.Game).all()


@app.get("/games/{game_id}")
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Игра не найдена")
    return game


@app.put("/games/{game_id}")
def update_game(game_id: int, data: schemas.GameUpdate, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Игра не найдена")
    if data.title is not None:
        game.title = data.title
    if data.status is not None:
        game.status = data.status
    db.commit(); db.refresh(game)
    return game


@app.delete("/games/{game_id}")
def delete_game(game_id: int, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Игра не найдена")
    db.delete(game); db.commit()
    return {"deleted": game_id}


# ---------- CRUD: КОМАНДЫ ----------

@app.post("/games/{game_id}/teams")
def create_team(game_id: int, data: schemas.TeamCreate, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Игра не найдена")
    # имена команд в одной игре не должны повторяться (регистр/пробелы неважны)
    new_name = data.name.strip()
    existing_teams = db.query(models.Team).filter(models.Team.game_id == game_id).all()
    if any(t.name.strip().lower() == new_name.lower() for t in existing_teams):
        raise HTTPException(400, "Команда с таким названием уже есть")
    team = models.Team(name=new_name, game_id=game_id)
    db.add(team); db.commit(); db.refresh(team)
    return team


@app.get("/games/{game_id}/teams")
def list_teams(game_id: int, db: Session = Depends(get_db)):
    return db.query(models.Team).filter(models.Team.game_id == game_id).all()


@app.put("/teams/{team_id}")
def update_team(team_id: int, data: schemas.TeamUpdate, db: Session = Depends(get_db)):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(404, "Команда не найдена")
    team.name = data.name
    db.commit(); db.refresh(team)
    return team


@app.delete("/teams/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(404, "Команда не найдена")
    db.delete(team); db.commit()
    return {"deleted": team_id}


# ---------- СПРАВОЧНИКИ (для интерфейса) ----------

@app.get("/round-types")
def round_types():
    return ROUND_TYPES


# ---------- ВОПРОС ДЛЯ ОДНОГО ТРЕКА ----------

def big_artwork(url):
    """iTunes отдаёт 100x100; заменяем на 600x600 для нормального качества."""
    if not url:
        return url
    return url.replace("100x100", "600x600")


def _make_question(round_type, track):
    """Возвращает (вопрос, правильный ответ, extra_text, speed) по типу раунда."""
    if round_type == "guess_artist":
        return "Прослушайте отрывок и назовите исполнителя.", track.artist, None, 1.0
    if round_type == "guess_cover":
        return "Посмотрите на обложку альбома и назовите исполнителя.", track.artist, None, 1.0
    if round_type == "by_lyrics":
        lines = get_lyrics_lines(track.artist, track.title, 8)
        if lines:
            return "Прочитайте отрывок текста и назовите песню.", track.title, lines, 1.0
        return None  # нет текста — пропускаем этот трек
    if round_type == "speed":
        return "Прослушайте ускоренный отрывок и назовите трек.", track.title, None, 1.8
    if round_type == "ai_fact":
        fact = make_fact(track.artist, track.title)
        if fact:
            return "Угадайте песню по подсказке от ИИ.", track.title, fact, 1.0
        return None  # ИИ не ответил — пропускаем трек
    # guess_track по умолчанию
    return "Прослушайте отрывок и назовите трек.", track.title, None, 1.0


# ---------- АВТОСБОРКА РАУНДА (тип + N разных треков) ----------

@app.post("/games/{game_id}/rounds/auto")
def auto_build_round(game_id: int, genre: str, round_type: str = "guess_track",
                     count: int = 10, db: Session = Depends(get_db)):
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Игра не найдена")

    teams = db.query(models.Team).filter(models.Team.game_id == game_id).all()
    if not teams:
        raise HTTPException(400, "Сначала добавьте команды")

    # число треков кратно числу команд
    n_teams = len(teams)
    if count % n_teams != 0:
        count = round(count / n_teams) * n_teams or n_teams

    # ИИ-раунды и «микс» не привязаны к жанру — берём из всех жанров
    ai_types = ("ai_fact", "by_lyrics")
    if genre == "mixed" or (round_type in ai_types and genre == "mixed"):
        queries = []
        for qs in GENRE_QUERIES.values():
            queries += qs
    else:
        queries = GENRE_QUERIES.get(genre)
    if not queries:
        raise HTTPException(400, "Неизвестный жанр")

    import random
    queries = list(queries)
    random.shuffle(queries)  # чтобы не всегда начинать с одного исполнителя

    # треки и исполнители, уже занятые в этой игре (не повторять между раундами)
    used_track_ids = set()
    used_artists = set()
    for rnd in game.rounds:
        for it in rnd.items:
            used_track_ids.add(it.track_id)
            # исполнителей между раундами НЕ блокируем — только конкретные треки

    # собираем кандидатов С ЗАПАСОМ (в 3 раза больше нужного),
    # т.к. для ИИ/текст-раундов часть треков может не подойти
    candidates = []
    seen_ids = set()
    seen_artists = set()
    target_candidates = count * 3
    for q in queries:
        found = search_tracks(q, limit=25)
        random.shuffle(found)
        saved = save_tracks(db, found)
        for t in saved:
            if t.id in used_track_ids or t.id in seen_ids:
                continue
            a = t.artist.lower()
            if a in seen_artists:
                continue  # один исполнитель — только раз в раунде
            seen_ids.add(t.id)
            seen_artists.add(a)
            candidates.append(t)
        if len(candidates) >= target_candidates:
            break

    if not candidates:
        raise HTTPException(400, "Треки не найдены (проверьте VPN)")

    number = db.query(models.Round).filter(models.Round.game_id == game_id).count() + 1
    base = ROUND_TYPES.get(round_type, {}).get("points", 100)
    rnd = models.Round(game_id=game_id, round_type=round_type, genre=genre,
                       number=number, base_points=base)
    db.add(rnd); db.commit(); db.refresh(rnd)

    # строим вопросы, ДОБИРАЯ замену пропущенным трекам из запаса кандидатов
    import time as _time
    ai_round = round_type in ("ai_fact",)
    made = 0
    leftover = []  # треки, где ИИ не сработал — пригодятся для запасного заполнения
    for track in candidates:
        if made >= count:
            break
        q = _make_question(round_type, track)
        if q is None:
            leftover.append(track)
            continue  # ИИ не ответил — попробуем следующего
        question, correct, extra, speed = q
        team = teams[made % len(teams)]
        item = models.RoundTrack(
            round_id=rnd.id, track_id=track.id, position=made, team_id=team.id,
            question_text=question, correct_answer=correct,
            extra_text=extra, speed=speed,
        )
        db.add(item)
        made += 1
        if ai_round:
            _time.sleep(0.5)  # пауза, чтобы не упереться в лимит частоты ИИ

    # если ИИ-раунд недобрал (лимит ИИ) — дозаполняем обычным вопросом «угадай трек»
    if made < count and ai_round:
        for track in leftover:
            if made >= count:
                break
            team = teams[made % len(teams)]
            item = models.RoundTrack(
                round_id=rnd.id, track_id=track.id, position=made, team_id=team.id,
                question_text="Прослушайте отрывок и назовите трек.",
                correct_answer=track.title, extra_text=None, speed=1.0,
            )
            db.add(item)
            made += 1
    db.commit()

    if made == 0:
        db.delete(rnd); db.commit()
        raise HTTPException(400, "Для этого жанра не нашлось подходящих треков "
                                 "(нет текстов/ИИ недоступен). Выберите другой жанр или тип.")

    return {"round_id": rnd.id, "number": rnd.number, "type": round_type, "tracks": made}


@app.delete("/rounds/{round_id}")
def delete_round(round_id: int, db: Session = Depends(get_db)):
    rnd = db.query(models.Round).filter(models.Round.id == round_id).first()
    if not rnd:
        raise HTTPException(404, "Раунд не найден")
    db.delete(rnd); db.commit()
    return {"deleted": round_id}


# ---------- ИГРОВОЙ ПРОЦЕСС ----------

@app.get("/games/{game_id}/rounds")
def game_rounds(game_id: int, db: Session = Depends(get_db)):
    """Список раундов игры с числом треков."""
    rounds = db.query(models.Round).filter(models.Round.game_id == game_id)\
        .order_by(models.Round.number).all()
    out = []
    for r in rounds:
        meta = ROUND_TYPES.get(r.round_type, {})
        genre_label = GENRE_LABELS.get(r.genre, r.genre or "")
        out.append({"round_id": r.id, "number": r.number, "type": r.round_type,
                    "label": meta.get("label", r.round_type),
                    "genre": genre_label,
                    "difficulty": meta.get("difficulty", ""),
                    "tracks": len(r.items)})
    return out


@app.put("/games/{game_id}/rounds/order")
def set_round_order(game_id: int, order: schemas.RoundOrder, db: Session = Depends(get_db)):
    """Задаёт порядок раундов: order.round_ids — список id в нужном порядке."""
    game = db.query(models.Game).filter(models.Game.id == game_id).first()
    if not game:
        raise HTTPException(404, "Игра не найдена")
    for new_number, rid in enumerate(order.round_ids, start=1):
        rnd = db.query(models.Round).filter(
            models.Round.id == rid, models.Round.game_id == game_id).first()
        if rnd:
            rnd.number = new_number
    db.commit()
    return {"ok": True}


@app.get("/rounds/{round_id}/track/{position}")
def get_round_track(round_id: int, position: int, db: Session = Depends(get_db)):
    """Вернуть один трек раунда по позиции."""
    item = db.query(models.RoundTrack).filter(
        models.RoundTrack.round_id == round_id,
        models.RoundTrack.position == position).first()
    if not item:
        raise HTTPException(404, "Трек не найден")
    total = db.query(models.RoundTrack).filter(
        models.RoundTrack.round_id == round_id).count()
    meta = ROUND_TYPES.get(item.round.round_type, {})
    rtype = item.round.round_type

    # Что показывать/играть ДО ответа, по типу раунда:
    is_cover = rtype == "guess_cover"
    is_text = rtype in ("by_lyrics", "ai_fact")  # только текст
    is_speed = rtype == "speed"

    preview_before = None
    if not is_cover and not is_text:
        preview_before = item.track.preview_url  # обычные и ускоренный играют трек

    return {
        "round_track_id": item.id,
        "position": item.position,
        "total": total,
        "question": item.question_text,
        "text_before": item.extra_text if is_text else None,  # текст/загадка/перевод
        "team_id": item.team_id,
        "team_name": item.team.name if item.team else "",
        "round_type": rtype,
        "difficulty": meta.get("difficulty", ""),
        "speed": item.speed or 1.0,
        # ДО ответа
        "preview_before": preview_before,
        "artwork_before": big_artwork(item.track.artwork_url) if is_cover else None,
        # ПОСЛЕ ответа — раскрываем всё
        "preview_after": item.track.preview_url,
        "artwork_after": big_artwork(item.track.artwork_url),
        "reveal_title": item.track.title,
        "reveal_artist": item.track.artist,
        "reveal_text": item.extra_text,  # текст/перевод/загадка показать в ответе
    }


@app.post("/round-tracks/{round_track_id}/answer")
def answer_round_track(round_track_id: int, data: schemas.AnswerSubmit,
                       db: Session = Depends(get_db)):
    item = db.query(models.RoundTrack).filter(
        models.RoundTrack.id == round_track_id).first()
    if not item:
        raise HTTPException(404, "Трек не найден")

    rtype = item.round.round_type
    # раунды по исполнителю: засчитываем любого из исполнителей, баллы за каждого
    if rtype in ("guess_artist", "guess_cover"):
        matched, total_artists, ok = check_artists(data.answer_text, item.track.artist)
        is_correct = ok
        if is_correct:
            base = item.round.base_points
            # баллы пропорционально угаданным исполнителям (минимум как за одного)
            pts_one = calculate_points(base, data.answer_time)
            points = int(pts_one * matched / max(total_artists, 1)) if total_artists > 1 else pts_one
            points = max(points, pts_one // total_artists) if total_artists > 1 else pts_one
        else:
            points = 0
        score = 100 if is_correct else 0
    else:
        is_correct, score = check_answer(data.answer_text, item.correct_answer)
        points = calculate_points(item.round.base_points, data.answer_time) if is_correct else 0

    ans = models.Answer(
        round_track_id=round_track_id, team_id=data.team_id,
        answer_text=data.answer_text, is_correct=is_correct,
        points=points, answer_time=data.answer_time,
    )
    db.add(ans); db.commit()

    # живой комментарий от ИИ (если доступен)
    team = db.query(models.Team).filter(models.Team.id == data.team_id).first()
    comment = comment_answer(team.name if team else "Команда",
                             is_correct, data.answer_text, item.correct_answer)

    return {"correct": is_correct, "points": points,
            "correct_answer": item.correct_answer,
            "comment": comment}


@app.get("/games/{game_id}/final")
def final(game_id: int, db: Session = Depends(get_db)):
    """Итоговое слово от ИИ по таблице лидеров."""
    rows = _leaderboard_rows(db, game_id)
    standings = [(r[0], int(r[1])) for r in rows]
    words = final_words(standings)
    return {"standings": standings, "words": words}


@app.get("/games/{game_id}/leaderboard")
def leaderboard(game_id: int, db: Session = Depends(get_db)):
    rows = _leaderboard_rows(db, game_id)
    return [{"team": r[0], "score": int(r[1])} for r in rows]
