import hashlib
import re
import json
import re
from decimal import Decimal

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from budget.models import Budget, ShoppingListItem
from voice.ai import call_openai
from voice.parser import (
    normalize,
    remaining_query,
    rules_parse,
    INTENT_BUDGET_PLAN,
    INTENT_HELP,
    INTENT_PRODUCT_SEARCH,
)
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
    prefer_rules = payload.get("prefer_rules", False)
    mode = payload.get("mode", "")
    normalized = normalize(text)

    parsed_schema = rules_parse(normalized)
    if prefer_rules and parsed_schema.get("intent") == INTENT_HELP and normalized:
        parsed_schema["intent"] = INTENT_PRODUCT_SEARCH
        parsed_schema["entities"]["query"] = remaining_query(normalized)
        parsed_schema["confidence"] = max(parsed_schema.get("confidence", 0), 0.7)
    if prefer_rules and parsed_schema.get("intent") == INTENT_BUDGET_PLAN:
        if not parsed_schema["entities"].get("items"):
            items_text = remaining_query(normalized)
            if items_text:
                items = [
                    item.strip()
                    for item in re.split(r"\band\b|,", items_text)
                    if item.strip()
                ]
                parsed_schema["entities"]["items"] = items[:20]
    if mode == "budget" and parsed_schema.get("intent") == INTENT_HELP and normalized:
        parsed_schema["intent"] = INTENT_BUDGET_PLAN
    if mode == "budget" and not parsed_schema["entities"].get("items"):
        items_text = remaining_query(normalized)
        if items_text:
            items = [
                item.strip()
                for item in re.split(r"\band\b|,", items_text)
                if item.strip()
            ]
            parsed_schema["entities"]["items"] = items[:20]
    if mode == "budget":
        amount = parsed_schema["entities"].get("amount")
        if amount is None:
            cached_amount = request.session.get("voice_budget_amount")
            if cached_amount is not None:
                parsed_schema["entities"]["amount"] = cached_amount
        else:
            request.session["voice_budget_amount"] = amount
    nearby_only = "near me" in normalized
    schema = parsed_schema

    cache_key = None
    if requires_ai(parsed_schema) and not prefer_rules:
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
    budget_record = None
    if mode == "budget" and request.user.is_authenticated:
        amount = request.session.get("voice_budget_amount")
        if amount is not None:
            budget_record = Budget.get_active_for_user(request.user)
            if budget_record is None:
                budget_record = Budget.objects.create(
                    user=request.user,
                    total_budget=Decimal(str(amount)),
                )
            elif budget_record.total_budget != Decimal(str(amount)):
                budget_record.total_budget = Decimal(str(amount))
                budget_record.save(update_fields=["total_budget", "updated_at"])

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
        bundles, message, selected_products, missing_items = budget_plan(validated["entities"])
        if message:
            validated["intent"] = INTENT_HELP
            validated["assistant_message"] = message
        else:
            results["bundles"] = bundles
            if missing_items and not bundles:
                validated["assistant_message"] = (
                    "I couldn't find some products, but I added them to your shopping list."
                )
            else:
                validated["assistant_message"] = validated["assistant_message"] or "Here is a bundle within your budget."
            if budget_record is not None:
                for product in selected_products:
                    ShoppingListItem.objects.get_or_create(
                        budget=budget_record,
                        product=product,
                        name="",
                    )
                for item_name in missing_items:
                    ShoppingListItem.objects.get_or_create(
                        budget=budget_record,
                        product=None,
                        name=item_name,
                    )

    if validated["intent"] == INTENT_HELP and not validated["assistant_message"]:
        validated["assistant_message"] = "Please tell me what you want to buy or your budget."

    response_payload = {**validated, "results": results}
    if budget_record is not None:
        response_payload["budget_url"] = reverse("budget:view-budget", args=[budget_record.id])
    return JsonResponse(response_payload)
