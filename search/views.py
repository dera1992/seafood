from django.db.models import Q, Count, Avg
from django.shortcuts import render, get_object_or_404
from foodCreate.models import Products, Category, SubCategory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, Http404,HttpResponse, JsonResponse

from owner.models import Affiliate
from search.recommendations import get_recommended_products, get_user_location


def is_valid_queryparam(param):
    return param != '' and param is not None


def filter(request):
    qs = Products.objects.all()
    order = request.GET.get('order', '')
    view_mode = request.GET.get('view', 'list')
    affiliates = Affiliate.objects.all()[:10]
    # qs = qs.order_by(order)
    categories = Category.objects.all()
    subcategory = SubCategory.objects.all()
    is_favourite = False
    title_contains_query = request.GET.get('title_contains_query')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')
    category = request.GET.get('category')
    nearby_only = request.GET.get('nearby') == 'on'

    if is_valid_queryparam(title_contains_query):
        qs = qs.filter(Q(title__icontains=title_contains_query )
                       | Q(description__icontains=title_contains_query)
                       ).distinct()

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


    if is_valid_queryparam(date_min):
        qs = qs.filter(created_date__gte=date_min)

    if is_valid_queryparam(date_max):
        qs = qs.filter(created_date__lt=date_max)

    if is_valid_queryparam(category) and category != 'Choose...':
        qs = qs.filter(category__name=category)

    if nearby_only and request.user.is_authenticated:
        location = get_user_location(request.user)
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

    paginator = Paginator(qs, 2)  # Show 25 contacts per page
    page_request_var = "page"
    page = request.GET.get('page')
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        queryset = paginator.page(1)
    except EmptyPage:
        queryset = paginator.page(paginator.num_pages)

    context = {
        'queryset': queryset,'categories': categories,'is_favourite': is_favourite,
        'order': order,'page': page,'affiliates':affiliates,'view_mode': view_mode,
        'nearby_only': nearby_only

    }

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string("search/results.html", context, request=request)
        return JsonResponse({"html": html, "count": len(queryset)})

    return render(request, "search/main_search.html", context)


def product_recommendations(request):
    recommended_products, user_location = get_recommended_products(request.user)
    return render(
        request,
        "search/recommendations.html",
        {
            "recommended_products": recommended_products,
            "user_location": user_location,
        },
    )
