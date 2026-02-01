from copy import deepcopy

from voice.parser import (
    INTENT_BUDGET_PLAN,
    INTENT_HELP,
    INTENT_PRODUCT_SEARCH,
    CURRENCY,
    build_schema,
)

ALLOWED_INTENTS = {INTENT_PRODUCT_SEARCH, INTENT_BUDGET_PLAN, INTENT_HELP}


def _help_schema(message):
    schema = build_schema()
    schema["intent"] = INTENT_HELP
    schema["assistant_message"] = message
    return schema


def requires_ai(schema):
    if schema.get("intent") not in ALLOWED_INTENTS:
        return True
    if schema.get("confidence", 0) < 0.7:
        return True
    intent = schema.get("intent")
    entities = schema.get("entities") or {}
    if intent == INTENT_PRODUCT_SEARCH:
        return not (entities.get("query") or entities.get("items"))
    if intent == INTENT_BUDGET_PLAN:
        return not (entities.get("amount") and entities.get("items"))
    return True


def validate_schema(schema):
    validated = deepcopy(build_schema())
    if not schema or schema.get("intent") not in ALLOWED_INTENTS:
        return _help_schema("What would you like to do?"), False

    validated.update({
        "intent": schema.get("intent"),
        "confidence": float(schema.get("confidence", 0)),
        "source": schema.get("source", "rules"),
        "assistant_message": schema.get("assistant_message", ""),
    })

    entities = schema.get("entities") or {}
    validated["entities"] = {
        "query": entities.get("query", ""),
        "items": entities.get("items") or [],
        "amount": entities.get("amount"),
        "currency": CURRENCY,
        "max_price": entities.get("max_price"),
    }

    if validated["entities"]["amount"] is not None:
        amount = float(validated["entities"]["amount"])
        if amount <= 0 or amount > 100000:
            return _help_schema("Please say your budget amount in pounds"), False
        validated["entities"]["amount"] = amount

    if validated["entities"]["max_price"] is not None:
        max_price = float(validated["entities"]["max_price"])
        if max_price <= 0 or max_price > 100000:
            return _help_schema("Please say your budget amount in pounds"), False
        validated["entities"]["max_price"] = max_price

    items = validated["entities"]["items"]
    if len(items) > 20:
        return _help_schema("What items should I include?"), False
    for item in items:
        if len(item) > 50:
            return _help_schema("What items should I include?"), False

    if validated["intent"] == INTENT_PRODUCT_SEARCH:
        if not (validated["entities"]["query"] or items):
            return _help_schema("What items should I include?"), False

    if validated["intent"] == INTENT_BUDGET_PLAN:
        if validated["entities"]["amount"] is None:
            return _help_schema("Please say your budget amount in pounds"), False
        if not items:
            return _help_schema("What items should I include?"), False

    return validated, True
