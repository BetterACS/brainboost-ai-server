from dotenv import load_dotenv
load_dotenv()

import os
import fitz

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
from .models.response import CreatGameRequest

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        game_json = create_game(request)
        return {"status": 200, "data": game_json}
    
    except Exception as e:
        return {"status": 500, "data": f"Error occurs {e}"}
