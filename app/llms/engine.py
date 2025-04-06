from openai import OpenAI
import app.constraints as constraints
from app.models.response import QuizGameResponse, CreatGameRequest, YesNoGameResponse, BingoGameResponse, GameSelectionResponse
from app.models.games import QuizGameJson, YesNoGameJson, BingoGameJson
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

GAME_SELECTION = \
"""
Analyse this context what kind of game is match for this context.

context:
{context}

recommend guideline:
- 'quiz' : This is the common game all the context can use this template.
- 'yesno': The context recommend for this template is the context that can tell the story, long question, comparable.
- 'bingo': The context must contain a lots of technical term 'keywords'.

available game type:
- Please select one of these available template {types}.

answer:
Please answer with this format
"""

GAME_SETTINGS_DICT = {
    "quiz": {
        "format": "Q: {question}\nC1: {choice1}\nC2: {choice2}\nC3: {choice3}\nC4: {choice4}\nCA: {correct_answer_index}",
        "instructions": "- Create a {num} (if valid context) question (hard question).\n- Use the context above to generate the questions.",
    },
    "yesno": {
        "format": "Q: {question}\n correct_ans: {correct_ans}",
        "instructions": "- Create a {num} (if valid context) True / False question (hard question).\n- Use the context above to generate the questions.",
    },
    "bingo": {
        # 1 - 9
        'format': "Q1: {question}\nA1: {answer1}\nQ2: {question}\nA2: {answer2}\nQ3: {question}\nA3: {answer3}\nQ4: {question}\nA4: {answer4}\nQ5: {question}\nA5: {answer5}\nQ6: {question}\nA6: {answer6}\nQ7: {question}\nA7: {answer7}\nQ8: {question}\nA8: {answer8}\nQ9: {question}\nA9: {answer9}",
        'instructions': "- Create 9 question and its answers. \nThe answer must be a 'keywords'. (Because the calculate score is exact match!)"
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
- If the value is not a string do not change it.
"""

def get_response_type(game_type: str):
    if game_type == 'quiz':
        return QuizGameResponse
    elif game_type == 'yesno':
        return YesNoGameResponse
    elif game_type == 'bingo':
        return BingoGameResponse
    else:
        raise ValueError(f"game_type '{game_type}' is not support")

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
        elif isinstance(g, YesNoGameJson):
            results.append({
                "game_type": 'yesno',
                "content": {
                    "correct_ans": g.correct_ans,
                    "question": g.question
                },
            })
        elif isinstance(g, BingoGameJson):
            results.append({
                "game_type": 'bingo',
                "content": {
                    "questions": g.questions,
                    "answers": g.answers
                },
            })

    return results

# @app.post("/create_game")
# def create_game(request: CreatGameRequest):
def create_game(game_types: str, num_games: int, context: str, personalize_instructions: str, language: str):
    client = OpenAI()
    completion = client.beta.chat.completions.parse(
        model=constraints.OPENAI_MODEL_NAME,
        messages=[
            {"role": "user", "content": GAME_SELECTION.format(context=context, types=game_types) + "\n" + "{type: ...}"},
        ],
        response_format=GameSelectionResponse,
    )

    # game_type = request.game_type
    game_type = completion.choices[0].message.parsed.type
    print(f"Making Game: {game_type}")

    game_settings = GAME_SETTINGS_DICT[game_type]
    instructions = game_settings["instructions"].format(num=num_games)

    prompt = CREATE_GAME_PROMPT.format(
        context=context, instructions=instructions, format=game_settings['format'], game_type=game_type, lang=language
    )

    completion = client.chat.completions.create(
        model=constraints.OPENAI_MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )

    game_str = completion.choices[0].message.content
    refined_game_str = refine_game(context=game_str, personalize_instructions=personalize_instructions)
    print(refined_game_str)
    game_json = construction_json(game_type=game_type, context=refined_game_str)
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


def explain(context: str):
    client = OpenAI()
    completion = client.chat.completions.create(
        model=constraints.OPENAI_MODEL_NAME,
        messages=[{"role": "user", "content": context}],
    )

    completion = completion.choices[0].message.content
    return completion
