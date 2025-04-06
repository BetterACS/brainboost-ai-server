from pydantic import BaseModel
from typing import List
from app.models.games import QuizGameJson, YesNoGameJson, BingoGameJson

class YesNoGameResponse(BaseModel):
    games: List[YesNoGameJson] 

class QuizGameResponse(BaseModel):
    games: List[QuizGameJson]

class BingoGameResponse(BaseModel):
    games: List[BingoGameJson]

class CreatGameRequest(BaseModel):
    request_type: str
    # game_types: List[str]
    # num_games: int
    context: str
    language: str
    personalize: str

class GameSelectionResponse(BaseModel):
    type: str

# class SummarizeRequest(BaseModel):
#     context: str
