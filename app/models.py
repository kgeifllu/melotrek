from datetime import datetime

#описание таблиц базы данных

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="created")

    teams = relationship("Team", back_populates="game", cascade="all, delete-orphan")
    rounds = relationship("Round", back_populates="game", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    game_id = Column(Integer, ForeignKey("games.id"))

    game = relationship("Game", back_populates="teams")
    answers = relationship("Answer", back_populates="team", cascade="all, delete-orphan")


class Track(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    preview_url = Column(String)
    artwork_url = Column(String)
    year = Column(String)
    genre = Column(String)


class Round(Base):
    """Раунд-контейнер: один тип вопроса + набор треков внутри."""
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    round_type = Column(String, default="guess_track")
    genre = Column(String, default="")
    number = Column(Integer, default=1)
    base_points = Column(Integer, default=100)

    game = relationship("Game", back_populates="rounds")
    items = relationship("RoundTrack", back_populates="round",
                         cascade="all, delete-orphan", order_by="RoundTrack.position")


class RoundTrack(Base):
    """Один трек внутри раунда: вопрос, ответ, позиция, назначенная команда."""
    __tablename__ = "round_tracks"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"))
    track_id = Column(Integer, ForeignKey("tracks.id"))
    position = Column(Integer, default=0)
    team_id = Column(Integer, ForeignKey("teams.id"))
    question_text = Column(Text)
    correct_answer = Column(String)
    extra_text = Column(Text)          # текст песни / загадка ИИ / перевод — что показать
    speed = Column(Float, default=1.0) # скорость проигрывания (для ускоренного раунда)

    round = relationship("Round", back_populates="items")
    track = relationship("Track")
    team = relationship("Team")
    answers = relationship("Answer", back_populates="round_track",
                           cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    round_track_id = Column(Integer, ForeignKey("round_tracks.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    answer_text = Column(String)
    is_correct = Column(Boolean, default=False)
    points = Column(Integer, default=0)
    answer_time = Column(Float, default=0.0)

    round_track = relationship("RoundTrack", back_populates="answers")
    team = relationship("Team", back_populates="answers")
