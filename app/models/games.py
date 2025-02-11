from pydantic import BaseModel
from typing import List

class QuizGameJson(BaseModel):
    question: str
    choices: List[str]
    correct_index: int
