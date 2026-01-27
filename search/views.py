from django.db.models import Q, Count
from django.shortcuts import render, get_object_or_404
from foodCreate.models import Products, Category, SubCategory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect, Http404,HttpResponse, JsonResponse

from owner.models import Affiliate


def is_valid_queryparam(param):
    return param != '' and param is not None


def filter(request):
    qs = Products.objects.all()
    order = request.GET.get('order', '')
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

    if is_valid_queryparam(title_contains_query):
        qs = qs.filter(Q(title__icontains=title_contains_query )
                       | Q(description__icontains=title_contains_query)
                       ).distinct()

    if is_valid_queryparam(price_min):
        qs = qs.filter(price__gte=price_min)

    if is_valid_queryparam(price_max):
        qs = qs.filter(price__lt=price_max)


    if is_valid_queryparam(date_min):
        qs = qs.filter(created_date__gte=date_min)

    if is_valid_queryparam(date_max):
        qs = qs.filter(created_date__lt=date_max)

    if is_valid_queryparam(category) and category != 'Choose...':
        qs = qs.filter(category__name=category)


    if order == "price":
        qs = qs.order_by(order)
    elif order == "-price":
        qs = qs.order_by(order)
    elif order == "-created_date":
        qs = qs.order_by(order)

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
        'order': order,'page': page,'affiliates':affiliates

    }

    return render(request, "search/main_search.html", context)
