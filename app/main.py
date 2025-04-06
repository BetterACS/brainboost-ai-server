from dotenv import load_dotenv
load_dotenv()

import os
import torch
import fitz
import random
from google import genai

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image
from tqdm import tqdm
from openai import OpenAI
from pydantic import BaseModel
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache
from .extractor import get_extractor, extract_text_from_pdf
from .llms.engine import create_game, explain
from .utils.chunking import sliding_window_chunking, get_chunk_distribution
from .models.response import CreatGameRequest

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

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
    request_type = request.request_type

    if request_type == 'full':
        min_chunks = 5
        chunks_size = 4200
        overlap_size = 200
        max_questions = 20
        min_questions = 12
        
    elif request_type == 'partial':
        min_chunks = 2
        chunks_size = 3000
        overlap_size = 200
        max_questions = 8
        min_questions = 5
    
    else:
        raise {"status": 500, "data": "Invalid request type."}
    
    
    try:
        context = request.context
        game_types = "'quiz', 'yesno', 'bingo'"

        yesno_quota = 5

        if len(context) < 100:
            return {"status": 500, "data": "Context is too small."}

        # 20 games 10 chunks (avg 2 questions per chunk)
        # chunks = sliding_window_chunking(context, chunk_size=chunks_size, overlap_size=100)
        chunks, question_distribution = get_chunk_distribution(min_chunks, max_questions, min_questions, context, overlap_size, chunks_size)
        print(f"Chunks: {len(chunks)}")

        game_json = []
        for chunk, num_games in tqdm(zip(chunks, question_distribution), desc="Creating games..", total=len(chunks)):
            if len(chunk) < 100:
                # Skip small chunk.
                continue

            _request = request
            _request.context = chunk
            # _request.num_games = num_games
            game = create_game(game_types=game_types, num_games=num_games, context=chunk, personalize_instructions=request.personalize, language=request.language)
            
            if game[0]['game_type'] == "bingo":
                game_types = game_types.replace("'bingo'", "")

            if game[0]['game_type'] == "yesno":
                yesno_quota -= 1
                if yesno_quota <= 0:
                    game_types = game_types.replace("'yesno'", "")

            game_json.extend(game)


        if len(game_json) == 0:
            return {"status": 500, "data": "No game created from the context due to small context size."}

        return {"status": 200, "data": game_json}

    except Exception as e:
        return {"status": 500, "data": f"Error occurs {e}"}

@app.get("/explain_answer")
def explain_answer(context: str):
    answer = explain(context)
    return {"status": 200, "data": answer}

@app.get("/get_similarity")
def get_similarity(context1: str, context2: str):
    try:
        result = client.models.embed_content(model="gemini-embedding-exp-03-07", contents=[context1, context2])

        text_tensor_1 = torch.tensor(result.embeddings[0].valอues).unsqueeze(0)
        text_tensor_2 = torch.tensor(result.embeddings[1].values).unsqueeze(0)

        similarity = torch.nn.functional.cosine_similarity(text_tensor_1, text_tensor_2)
        return {"status": 200, "data": similarity.item()}
    except Exception as e:
        return {"status": 500, "data": f"Error occurs {e}"}

