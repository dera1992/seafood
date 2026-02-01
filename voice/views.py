import hashlib
import json

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from voice.ai import call_openai
from voice.parser import normalize, rules_parse, INTENT_BUDGET_PLAN, INTENT_HELP, INTENT_PRODUCT_SEARCH
from voice.services import budget_plan, product_search
from voice.validators import requires_ai, validate_schema

CACHE_TTL_SECONDS = 60 * 60 * 24


@ensure_csrf_cookie
def search_page(request):
    return render(request, "voice/search.html")


@ensure_csrf_cookie
def budget_page(request):
    return render(request, "voice/budget.html")


@require_POST
def interpret_voice(request):
    # Placeholder for django-ratelimit or similar throttling.
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        payload = {}
    text = payload.get("text", "")
    normalized = normalize(text)

    parsed_schema = rules_parse(normalized)
    nearby_only = "near me" in normalized
    schema = parsed_schema

    cache_key = None
    if requires_ai(parsed_schema):
        cache_key = f"voice_intent:gb:{hashlib.sha256(normalized.encode('utf-8')).hexdigest()}"
        cached = cache.get(cache_key)
        if cached:
            schema = cached
        else:
            schema = call_openai(text)

    validated, is_valid = validate_schema(schema)
    if schema.get("source") == "ai" and is_valid and cache_key:
        cache.set(cache_key, validated, CACHE_TTL_SECONDS)

    results = {}

    if validated["intent"] == INTENT_PRODUCT_SEARCH:
        results["products"] = product_search(
            validated["entities"],
            user=request.user,
            nearby_only=nearby_only,
        )
        if results["products"]:
            validated["assistant_message"] = validated["assistant_message"] or "Here are the products I found."
        else:
            validated["assistant_message"] = "No products matched. Try another search."

    elif validated["intent"] == INTENT_BUDGET_PLAN:
        bundles, message = budget_plan(validated["entities"])
        if message:
            validated["intent"] = INTENT_HELP
            validated["assistant_message"] = message
        else:
            results["bundles"] = bundles
            validated["assistant_message"] = validated["assistant_message"] or "Here is a bundle within your budget."

    if validated["intent"] == INTENT_HELP and not validated["assistant_message"]:
        validated["assistant_message"] = "Please tell me what you want to buy or your budget."

    response_payload = {**validated, "results": results}
    return JsonResponse(response_payload)
