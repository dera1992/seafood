from django.shortcuts import render, get_object_or_404
from foodCreate.models import Category, SubCategory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, Http404,HttpResponse, JsonResponse

from owner.models import Affiliate
from search.recommendations import get_recommended_products
from search.services import filter_products, is_valid_queryparam


def filter(request):
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

    qs = filter_products(
        query=title_contains_query,
        price_min=price_min,
        price_max=price_max,
        category=category,
        nearby_only=nearby_only,
        order=order,
        user=request.user,
    )

    if is_valid_queryparam(date_min):
        qs = qs.filter(created_date__gte=date_min)

    if is_valid_queryparam(date_max):
        qs = qs.filter(created_date__lt=date_max)

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
