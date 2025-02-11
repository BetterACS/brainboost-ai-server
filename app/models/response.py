from pydantic import BaseModel
from typing import List
from app.models.games import QuizGameJson

class QuizGameResponse(BaseModel):
    games: List[QuizGameJson]

class CreatGameRequest(BaseModel):
    game_type: str
    context: str
    num_games: int
    language: str
    personalize: str
