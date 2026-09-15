from pydantic import BaseModel

# проверка входных данных

class GameCreate(BaseModel):
    title: str


class GameUpdate(BaseModel):
    title: str | None = None
    status: str | None = None


class TeamCreate(BaseModel):
    name: str


class TeamUpdate(BaseModel):
    name: str


class AnswerSubmit(BaseModel):
    team_id: int
    answer_text: str
    answer_time: float = 0.0


class RoundOrder(BaseModel):
    round_ids: list[int]
