import re
from decimal import Decimal

INTENT_PRODUCT_SEARCH = "PRODUCT_SEARCH"
INTENT_BUDGET_PLAN = "BUDGET_PLAN"
INTENT_HELP = "HELP"

CURRENCY = "GBP"

FILLER_PHRASES = [
    "please",
    "help me",
    "i want",
    "show me",
    "can you",
    "could you",
    "would you",
]

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
}

PRODUCT_KEYWORDS = [
    "find",
    "search",
    "show",
    "look for",
    "get",
]

BUDGET_KEYWORDS = [
    "budget",
    "i have",
    "i can spend",
    "i can afford",
    "not more than",
    "help me buy",
]

COMMON_ITEMS = [
    "rice",
    "fish",
    "catfish",
    "tomatoes",
    "tomato",
    "pepper",
    "crayfish",
    "chicken",
    "beef",
    "goat",
    "onion",
    "garlic",
    "ginger",
    "oil",
    "jollof",
    "plantain",
    "egg",
    "eggs",
    "salt",
    "seasoning",
    "prawn",
    "shrimp",
    "yam",
    "potato",
    "rice flour",
    "beans",
    "maize",
]


def build_schema():
    return {
        "intent": INTENT_HELP,
        "entities": {
            "query": "",
            "items": [],
            "amount": None,
            "currency": CURRENCY,
            "max_price": None,
        },
        "confidence": 0.0,
        "source": "rules",
        "assistant_message": "",
    }


def normalize(text):
    if not text:
        return ""
    normalized = text.lower()
    normalized = normalized.replace("£", " gbp ")
    normalized = re.sub(r"\b(pounds?|quid)\b", " gbp ", normalized)

    normalized = re.sub(r"\b(\d+)\s*k\b", lambda m: str(int(m.group(1)) * 1000), normalized)

    for word, value in sorted(NUMBER_WORDS.items(), key=lambda item: -len(item[0])):
        normalized = re.sub(rf"\b{word}\b", str(value), normalized)

    for phrase in FILLER_PHRASES:
        normalized = re.sub(rf"\b{re.escape(phrase)}\b", "", normalized)

    normalized = re.sub(r"[^a-z0-9\s]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _extract_amount(text):
    patterns = [
        r"i have\s+(\d+(?:\.\d+)?)\s*gbp",
        r"budget\s+(\d+(?:\.\d+)?)(?:\s*gbp)?",
        r"\bgbp\s*(\d+(?:\.\d+)?)\b",
        r"\b(\d+(?:\.\d+)?)\s*gbp\b",
        r"i have\s+(\d+(?:\.\d+)?)\b",
        r"budget\s+(\d+(?:\.\d+)?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return Decimal(match.group(1))
    return None


def _extract_max_price(text):
    patterns = [
        r"under\s+(\d+(?:\.\d+)?)\s*gbp?",
        r"under\s+gbp\s*(\d+(?:\.\d+)?)",
        r"under\s+(\d+(?:\.\d+)?)\b",
        r"less than\s+(\d+(?:\.\d+)?)\s*gbp?",
        r"less than\s+gbp\s*(\d+(?:\.\d+)?)",
        r"less than\s+(\d+(?:\.\d+)?)\b",
        r"max\s+(\d+(?:\.\d+)?)\s*gbp?",
        r"max\s+gbp\s*(\d+(?:\.\d+)?)",
        r"max\s+(\d+(?:\.\d+)?)\b",
        r"not more than\s+(\d+(?:\.\d+)?)\s*gbp?",
        r"not more than\s+gbp\s*(\d+(?:\.\d+)?)",
        r"not more than\s+(\d+(?:\.\d+)?)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return Decimal(match.group(1))
    return None


def _extract_items(text):
    found = []
    for item in COMMON_ITEMS:
        if re.search(rf"\b{re.escape(item)}\b", text):
            found.append(item)
    if found:
        return sorted(set(found), key=found.index)
    return []


def _intent_from_text(text):
    for phrase in BUDGET_KEYWORDS:
        if re.search(rf"\b{re.escape(phrase)}\b", text):
            return INTENT_BUDGET_PLAN, True
    for phrase in PRODUCT_KEYWORDS:
        if re.search(rf"\b{re.escape(phrase)}\b", text):
            return INTENT_PRODUCT_SEARCH, True
    return INTENT_HELP, False


def _remaining_query(text):
    cleaned = text
    for phrase in BUDGET_KEYWORDS + PRODUCT_KEYWORDS:
        cleaned = re.sub(rf"\b{re.escape(phrase)}\b", "", cleaned)
    cleaned = re.sub(r"\bgbp\b", "", cleaned)
    cleaned = re.sub(r"\bnear me\b", "", cleaned)
    cleaned = re.sub(r"\b\d+(?:\.\d+)?\b", "", cleaned)
    cleaned = re.sub(r"\bunder\b|\bless than\b|\bmax\b|\bnot more than\b", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def remaining_query(text):
    return _remaining_query(text)


def rules_parse(text):
    schema = build_schema()
    if not text:
        schema["assistant_message"] = "Please tell me what you are looking for."
        return schema

    intent, intent_hit = _intent_from_text(text)
    schema["intent"] = intent

    amount = _extract_amount(text)
    max_price = _extract_max_price(text)
    items = _extract_items(text)

    if items:
        schema["entities"]["items"] = items
    if amount is not None:
        schema["entities"]["amount"] = float(amount)
    if max_price is not None:
        schema["entities"]["max_price"] = float(max_price)

    if not schema["entities"]["items"]:
        schema["entities"]["query"] = _remaining_query(text)

    confidence = 0.0
    if intent_hit:
        confidence += 0.4
    if schema["intent"] == INTENT_BUDGET_PLAN and amount is not None:
        confidence += 0.3
    if schema["entities"]["items"]:
        confidence += 0.2
    if max_price is not None:
        confidence += 0.1

    schema["confidence"] = min(1.0, confidence)
    schema["source"] = "rules"
    return schema
