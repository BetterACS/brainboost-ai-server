from pydantic import BaseModel
from typing import List, Tuple

class QuizGameJson(BaseModel):
    question: str
    choices: List[str]
    correct_index: int

class YesNoGameJson(BaseModel):
    question: str
    correct_ans: bool 

class BingoGameJson(BaseModel):
    questions: List[str]
    answers: List[str]
