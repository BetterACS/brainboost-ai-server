from openai import OpenAI
import app.constraints as constraints
from app.models.response import QuizGameResponse, CreatGameRequest, SummarizeRequest
from app.models.games import QuizGameJson
from dotenv import load_dotenv

load_dotenv()
    
JSON_CONSTRUCTION_PROMPT = \
"""
You need to re-construct context to json format.
{context}
"""

CREATE_GAME_PROMPT = \
"""
Use the following context to generate a {game_type} game.

context:
```
{context}
```

You need to follow this game format:
```
{format}
```

Instructions:
- Please ignore class information like schedule, lecturer, etc.
- The 'question' should be not mentioned the context.
- The 'question' should use single language do not mix with other languages (Technical terms are allowed).
- Use {lang} language.
{instructions}

# Note: Leave it empty '[]' if the context is not valid.
"""

GAME_SETTINGS_DICT = {
    "quiz": {
        "format": "Q: {question}\nC1: {choice1}\nC2: {choice2}\nC3: {choice3}\nC4: {choice4}\nCA: {correct_answer_index}",
        "instructions": "- Create a {num} (if valid context) question (hard question).\n- Use the context above to generate the questions.",
    }
}

PERSONALIZE_PROMPT = \
"""
Personalize the following context.

context:
```
{context}
```

Personalize:
{personalize_instructions}

Instructions:
- Do not change the json format just paraphrase the question or answer.
"""

def get_response_type(game_type: str):
    if game_type == 'quiz':
        return QuizGameResponse
    else:
        raise ValueError(f"game_type '{game_type}' is not suppor")

def construction_json(game_type: str, context: str):
    response_type = get_response_type(game_type=game_type)
    
    client = OpenAI()    
    completion = client.beta.chat.completions.parse(
        model=constraints.OPENAI_MODEL_NAME,
        messages=[
            {"role": "user", "content": JSON_CONSTRUCTION_PROMPT.format(context=context)},
        ],
        response_format=response_type,
    )

    game_json = completion.choices[0].message.parsed
    results = []

    for g in game_json.games:
        if isinstance(g, QuizGameJson):
            results.append({
                "game_type": 'quiz',
                "content": {
                    "choices": g.choices, 
                    "correct_idx": g.correct_index,
                    "question": g.question
                },
            })
    
    return results

# @app.post("/create_game")
def create_game(request: CreatGameRequest):
    game_settings = GAME_SETTINGS_DICT[request.game_type]
    instructions = game_settings["instructions"].format(num=request.num_games)
    
    prompt = CREATE_GAME_PROMPT.format(
        context=request.context, instructions=instructions, format=game_settings['format'], game_type=request.game_type, lang=request.language
    )

    client = OpenAI()
    completion = client.chat.completions.create(
        model=constraints.OPENAI_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    
    game_str = completion.choices[0].message.content
    refined_game_str = refine_game(context=game_str, personalize_instructions=request.personalize)

    game_json = construction_json(game_type=request.game_type, context=refined_game_str)
    return game_json

def refine_game(context: str, personalize_instructions: str):
    prompt = PERSONALIZE_PROMPT.format(context=context, personalize_instructions=personalize_instructions )

    client = OpenAI()
    completion = client.chat.completions.create(
        model=constraints.OPENAI_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    
    game_str = completion.choices[0].message.content
    return game_str
