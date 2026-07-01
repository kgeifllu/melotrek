from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Boolean, Float, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship

from app.database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="created")  # created / active / finished

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
    external_id = Column(String, unique=True, index=True)  # id трека в iTunes
    title = Column(String, nullable=False)
    artist = Column(String, nullable=False)
    preview_url = Column(String)
    artwork_url = Column(String)
    year = Column(String)
    genre = Column(String)

    rounds = relationship("Round", back_populates="track")


class Round(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    track_id = Column(Integer, ForeignKey("tracks.id"))
    round_type = Column(String, default="guess_track")
    number = Column(Integer, default=1)
    base_points = Column(Integer, default=100)
    question_data = Column(String)  # спрятанное слово / переписанный текст и т.п.

    game = relationship("Game", back_populates="rounds")
    track = relationship("Track", back_populates="rounds")
    answers = relationship("Answer", back_populates="round", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("rounds.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    answer_text = Column(String)
    is_correct = Column(Boolean, default=False)
    points = Column(Integer, default=0)
    answer_time = Column(Float, default=0.0)  # секунд на ответ

    round = relationship("Round", back_populates="answers")
    team = relationship("Team", back_populates="answers")
