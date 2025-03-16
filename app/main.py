from dotenv import load_dotenv
load_dotenv()

import os
import fitz
import random

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from tqdm import tqdm
from openai import OpenAI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache
from .extractor import get_extractor, extract_text_from_pdf
from .llms.engine import create_game
from .models.response import CreatGameRequest, SummarizeRequest

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def sliding_window_chunking(text, chunk_size, overlap_size):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(''.join(text[start:end]))
        start += chunk_size - overlap_size

    return chunks

@lru_cache(maxsize=1)
def extractor():
    return get_extractor()

@app.get("/")
def hello():
    return {"message": "Hello World"}

@app.get("/extract")
def extract_pdf_files(pdf_path: str):
    try:
        markdown = extract_text_from_pdf(pdf_path, extractor())
        return {"status": 200, "data": markdown}
    
    except Exception as e:
        return {"status": 500, "data": f"Error occurs {e}"}

@app.post("/create_game")
def create_game_post(request: CreatGameRequest):
    overlap_size = 200
    max_questions = 20
    min_questions = 12

    min_chunks = 5
    chunks_size = 4200 

    try:
        context = request.context

        if len(context) < 100:
            return {"status": 500, "data": "Context is too small."}

        # 20 games 10 chunks (avg 2 questions per chunk)     
        # chunks = sliding_window_chunking(context, chunk_size=chunks_size, overlap_size=100)
        chunks = []
        while len(chunks) < min_chunks:
            if chunks_size < 500:
                return {"status": 500, "data": "Context is too small."}
            
            chunks = sliding_window_chunking(context, chunk_size=chunks_size, overlap_size=overlap_size)
            chunks_size -= int(chunks_size // 2.5)
            overlap_size -= 30
   
        # Max 10 chunks
        if len(chunks) > 10:
            chunks = random.sample(chunks, 10)
        
        min_q = 1
        max_q = 3

        question_distribution = [random.randint(min_q, max_q) for _ in range(len(chunks))]

        # Adjust if total exceeds max_questions
        while sum(question_distribution) > max_questions:
            for i in range(len(question_distribution)):
                if question_distribution[i] > min_q and sum(question_distribution) > max_questions:
                    question_distribution[i] -= 1

        # Adjust if total is less than min_questions
        while sum(question_distribution) < min_questions:
            for i in range(len(question_distribution)):
                if question_distribution[i] < max_q and sum(question_distribution) < min_questions:
                    question_distribution[i] += 1
        
        game_json = []
        for chunk, num_games in tqdm(zip(chunks, question_distribution), desc="Creating games..", total=len(chunks)):            
            print("Chunk size: ", len(chunk))

            # if len(chunk) < 300:
            #     print()
            #     # Skip small chunk.
            #     continue

            _request = request
            _request.context = chunk
            _request.num_games = num_games
            _request.game_type = "quiz"

            game_json.extend(create_game(_request))

        if len(game_json) == 0:
            return {"status": 500, "data": "No game created from the context due to small context size."}

        return {"status": 200, "data": game_json}
    
    except Exception as e:
        return {"status": 500, "data": f"Error occurs {e}"}

