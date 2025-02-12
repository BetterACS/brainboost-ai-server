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
from .llms.engine import create_game, create_summarize
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
    try:
        context = request.context
        chunks = sliding_window_chunking(context, chunk_size=4200, overlap_size=100)

        game_json = []
        for chunk in tqdm(chunks, desc="Creating games.."):
            _request = request
            _request.context = chunk
            _request.num_games = random.randint(2, 4)

            game_json.extend(create_game(_request))

        return {"status": 200, "data": game_json}
    
    except Exception as e:
        return {"status": 500, "data": f"Error occurs {e}"}

@app.post("/summarize")
def summarize(request: SummarizeRequest):
    try:
        context = request.context
        chunks = sliding_window_chunking(context, chunk_size=4200, overlap_size=100)

        summarized_contents = ""
        for chunk in tqdm(chunks, desc="Summarized contents.."):
            _request = request
            _request.context = chunk

            summarized_contents += "\n" + create_summarize(_request)
 
        return {"status": 200, "data": summarized_contents}

    except Exception as e:
        return {"status": 500, "data": f"Error occurs {e}"}
