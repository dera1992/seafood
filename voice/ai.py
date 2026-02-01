import importlib
import json
import os

from voice.parser import build_schema, CURRENCY, INTENT_BUDGET_PLAN, INTENT_HELP, INTENT_PRODUCT_SEARCH

ALLOWED_INTENTS = [INTENT_PRODUCT_SEARCH, INTENT_BUDGET_PLAN, INTENT_HELP]


def _openai_available():
    return importlib.util.find_spec("openai") is not None


def _build_prompt(text):
    return (
        "You are a voice assistant for a GBP-based ecommerce shop. "
        "Return ONLY JSON, no extra text. "
        f"Allowed intents: {', '.join(ALLOWED_INTENTS)}. "
        "Schema: {intent, entities:{query,items,amount,currency,max_price}, confidence, assistant_message}. "
        f"Currency must always be {CURRENCY}. "
        f"User text: {text}"
    )


def call_openai(text):
    schema = build_schema()
    if not _openai_available():
        schema["intent"] = INTENT_HELP
        schema["assistant_message"] = "Please tell me what you are looking for."
        return schema

    openai = importlib.import_module("openai")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        schema["intent"] = INTENT_HELP
        schema["assistant_message"] = "Please tell me what you are looking for."
        return schema

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Return ONLY JSON, no extra text."},
            {"role": "user", "content": _build_prompt(text)},
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        schema["intent"] = INTENT_HELP
        schema["assistant_message"] = "Please tell me what you are looking for."
        return schema

    data["source"] = "ai"
    return data
