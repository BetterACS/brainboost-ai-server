from openai import OpenAI
import app.constraints as constraints
from app.models.response import QuizGameResponse, CreatGameRequest
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
{instructions}
"""

GAME_SETTINGS_DICT = {
    "quiz": {
        "format": "Q: {question}\nC1: {choice1}\nC2: {choice2}\nC3: {choice3}\nC4: {choice4}\nCA: {correct_answer_index}",
        "instructions": "- Create a {num} question (hard question).\n- Use the context above to generate the questions.\n- Use {lang} language for the questions.\n"
    }
}


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
    instructions = game_settings["instructions"].format(num=request.num_games, lang=request.language) + request.personalize
    
    prompt = CREATE_GAME_PROMPT.format(
        context=request.context, instructions=instructions, format=game_settings['format'], game_type=request.game_type, 
    )

    client = OpenAI()
    completion = client.chat.completions.create(
        model=constraints.OPENAI_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )
    
    game_str = completion.choices[0].message.content
    game_json = construction_json(game_type=request.game_type, context=game_str)
    return game_json

    # try:
    #     # prompt = question_prompt.format(game_type=request.game_type, context=request.context, **game_settings[request.game_type])

    # except Exception as e:
    #     print(e)
    #     return {"status": 500, "message": "Error while Generate games", "data": []}

    # return {"status": 200, "message": "Create Game complete!", "data": game_json}
