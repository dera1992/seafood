from django.db.models import Q, Count, Avg

from foodCreate.models import Products
from search.recommendations import get_user_location


def is_valid_queryparam(param):
    return param != '' and param is not None


def filter_products(
    *,
    query=None,
    price_min=None,
    price_max=None,
    category=None,
    nearby_only=False,
    order=None,
    user=None,
):
    qs = Products.objects.all()

    if is_valid_queryparam(query):
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query)).distinct()

    if is_valid_queryparam(price_min):
        try:
            qs = qs.filter(price__gte=float(price_min))
        except ValueError:
            pass

    if is_valid_queryparam(price_max):
        try:
            qs = qs.filter(price__lt=float(price_max))
        except ValueError:
            pass

    if is_valid_queryparam(category) and category != 'Choose...':
        qs = qs.filter(category__name=category)

    if nearby_only and user and user.is_authenticated:
        location = get_user_location(user)
        if location.get("city"):
            qs = qs.filter(shop__city__iexact=location["city"])
        elif location.get("state"):
            qs = qs.filter(shop__state__iexact=location["state"])

    if order == "price":
        qs = qs.order_by("price")
    elif order == "-price":
        qs = qs.order_by("-price")
    elif order == "latest" or order == "-created_date":
        qs = qs.order_by("-created_date")
    elif order == "created_date":
        qs = qs.order_by("created_date")
    elif order == "discount_close":
        qs = qs.filter(discount_price__isnull=False).order_by("expires_on", "discount_price")
    elif order == "rating":
        qs = qs.annotate(avg_rating=Avg("reviewrating__rating")).order_by("-avg_rating")
    elif order == "best_selling":
        qs = qs.annotate(total_sold=Count("order_items")).order_by("-total_sold")

    return qs
