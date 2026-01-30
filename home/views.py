# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, redirect

from foodCreate.forms import ReviewForm
from foodCreate.models import Products, ProductsImages, Category, SubCategory, ReviewRating
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponseRedirect, Http404,HttpResponse, JsonResponse

from account.models import Profile, User, Shop, ShopFollower, ShopNotification
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from blog.models import Post
from cart.forms import CartAddProductForm
from django.views.decorators.http import require_POST
from order.models import OrderItem, Order
from star_ratings.models import Rating
from star_ratings.models import UserRating

from owner.models import Affiliate
from search.recommendations import get_recommended_products
from django.conf import settings
from home.models import WishlistItem, WishlistNotification

if settings.GIS_ENABLED:
    from django.contrib.gis.geos import Point
    from django.contrib.gis.db.models.functions import Distance
    from django.contrib.gis.measure import D
else:
    Point = None
    Distance = None
    D = None


@login_required
def dashboard(request, category_slug=None):
    category = None
    ads = Products.objects.all()
    latests = Products.objects.filter(available=True).order_by('-created_at', '?')[:6]
    categories = Category.objects.all()
    users = User.objects.all()
    blog = Post.objects.all()
    order = Order.objects.all()
    counts = Products.objects.all().values('category__name').annotate(total=Count('category'))

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        ads = ads.filter(category=category)
    return render(request,'home/dashboard.html', {'category': category,'categories': categories,'ads': ads,'latests':latests,
                                              'users':users,'blog':blog,'order':order})

def category_chart(request):
    labels = []
    data = []

    queryset = Products.objects.values('category__name').annotate(category_total=Count('category'))
    print(queryset)
    for entry in queryset:
        labels.append(entry['category__name'])
        data.append(entry['category_total'])

    return JsonResponse(data={
        'labels': labels,
        'data': data,
    })


def nearby_shops(request):
    if not settings.GIS_ENABLED:
        return JsonResponse(
            {"error": "Location-based search is unavailable because GIS support is disabled."},
            status=503,
        )
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius_km = request.GET.get("radius", 5)

    if not lat or not lng:
        return JsonResponse({"error": "Missing latitude or longitude."}, status=400)

    try:
        latitude = float(lat)
        longitude = float(lng)
        radius = float(radius_km)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid coordinate or radius values."}, status=400)

    user_location = Point(longitude, latitude, srid=4326)
    nearby = (
        Shop.objects.filter(location__isnull=False)
        .filter(location__distance_lte=(user_location, D(km=radius)))
        .annotate(distance=Distance("location", user_location))
        .order_by("distance")
    )

    shops = [
        {
            "name": shop.name,
            "address": shop.address,
            "city": shop.city,
            "distance_km": round(shop.distance.km, 2) if shop.distance else None,
        }
        for shop in nearby
    ]
    return JsonResponse({"shops": shops})

def home_list(request, category_slug=None):
    category = None
    excludes = ['Vegetables', 'Fruits', 'Grains', 'Seafood', 'Spices']
    ads = Products.objects.filter(
        available=True
    ).exclude(
        category__name__in=excludes
    ).order_by("?")[:6]
    ads_veg = Products.objects.filter(category__name='Vegetables',available=True).order_by("?")[:6]
    ads_fruits = Products.objects.filter(category__name='Fruits',available=True).order_by("?")[:6]
    ads_grains = Products.objects.filter(category__name='Grains',available=True).order_by("?")[:6]
    ads_seafood = Products.objects.filter(category__name='Seafood',available=True).order_by("?")[:6]
    ads_spices = Products.objects.filter(category__name='Spices', available=True).order_by("?")[:6]
    queryset_list = Post.objects.filter(draft=False).order_by('-timestamp', '?')[:3]
    latests = Products.objects.filter(available=True).order_by('-created_at', '?')[:6]
    affiliates = Affiliate.objects.all().order_by('-created', '?')[:10]
    qs = Products.objects.all()
    categories = Category.objects.all()
    subcategories = SubCategory.objects.all()
    recommended_products, user_location = get_recommended_products(request.user, limit=6)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        ads = ads.filter(category=category)
    return render(request,'home/index.html', {'category': category,'categories': categories,'ads': ads,'ads_veg':ads_veg,
                                              'ads_fruits':ads_fruits,'ads_grains':ads_grains,'ads_seafood':ads_seafood,
                                              'ads_spices':ads_spices,'latests':latests,
                                              'queryset': qs,'subcategories':subcategories,'queryset_list':queryset_list,
                                              'affiliates':affiliates,'recommended_products': recommended_products,
                                              'recommended_location': user_location})


def shop_list(request):
    view_mode = request.GET.get("view", "list")
    query = (request.GET.get("q") or "").strip()
    shops = (
        Shop.objects.filter(is_active=True)
        .select_related("owner")
        .annotate(product_count=Count("products"))
    )
    if query:
        shops = shops.filter(
            Q(name__icontains=query)
            | Q(address__icontains=query)
            | Q(city__icontains=query)
            | Q(state__icontains=query)
        )
    return render(
        request,
        "home/shop_list.html",
        {
            "shops": shops,
            "query": query,
            "view_mode": view_mode,
        },
    )


def shop_detail(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id, is_active=True)
    products = (
        Products.objects.filter(shop=shop, available=True)
        .select_related("category")
        .order_by("-created_at")
    )
    is_shop_subscribed = False
    if request.user.is_authenticated:
        is_shop_subscribed = ShopFollower.objects.filter(
            user=request.user, shop=shop
        ).exists()
    return render(
        request,
        "home/shop_detail.html",
        {
            "shop": shop,
            "products": products,
            "is_shop_subscribed": is_shop_subscribed,
        },
    )

def ads_list(request, category_slug=None):
    category = None
    ad_list = Products.objects.filter(available=True)
    order = request.GET.get('order', '-created_date')
    view_mode = request.GET.get('view', 'list')
    ad_list = ad_list.order_by(order)
    latests = Products.objects.filter(available=True).order_by('-created_at', '?')[:6]
    affiliates = Affiliate.objects.all()[:10]
    qs = Products.objects.all()
    categories = Category.objects.all()

    is_favourite = False

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        ad_list = ad_list.filter(category=category)

    paginator = Paginator(ad_list, 2)
    page_request_var = "page"
    page = request.GET.get('page')
    try:
        ads = paginator.page(page)
    except PageNotAnInteger:
        ads = paginator.page(1)
    except EmptyPage:
        ads = paginator.page(paginator.num_pages)
    return render(request,'search/main_search.html', {'category': category,'categories': categories,'queryset': ads,'latests':latests,
                                              'is_favourite': is_favourite,'order': order,'page': page,
                                              'affiliates':affiliates,'view_mode': view_mode})

# admin ad list
def allads_list(request, category_slug=None):
    category = None
    ad_list = Products.objects.all().order_by('-created_at', '?')
    categories = Category.objects.all()
    states = Products.objects.all()
    query = request.GET.get('q')
    if query:
        ad_list = ad_list.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(shop__name__icontains=query)
        )

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        ad_list = ad_list.filter(category=category)

    paginator = Paginator(ad_list, 10)
    page_request_var = "page"
    page = request.GET.get('page')
    try:
        ads = paginator.page(page)
    except PageNotAnInteger:
        ads = paginator.page(1)
    except EmptyPage:
        ads = paginator.page(paginator.num_pages)
    return render(request,'home/allads_list.html', {'category': category,'categories': categories,'ads': ads,
                                              'states':states,})


def ad_detail(request, id, slug):
    ad = get_object_or_404(Products,
                                id=id,
                                slug=slug,
                                available=True)
    adsimage = ProductsImages.objects.filter(products=ad)
    ad_similar = Products.objects.filter(category=ad.category).exclude(id=ad.id).order_by('?')[:7]
    latests = Products.objects.filter(available=True).order_by('-created_at', '?')[:6]
    profile = Profile.objects.filter(user=ad.shop.owner).first()
    categories = Category.objects.all()
    reviews = ReviewRating.objects.filter(post_id=ad.id, status=True)
    affiliates = Affiliate.objects.all()[:10]
    try:
        rating = Rating.objects.get(object_id=ad.id)
    except Rating.DoesNotExist:
        rating = None
    user_rating = UserRating.objects.filter(rating__object_id=ad.id)
    is_favourite = False
    is_shop_subscribed = False

    if request.user.is_authenticated and ad.favourite.filter(id=request.user.id).exists():
        is_favourite = True
    if request.user.is_authenticated:
        is_shop_subscribed = ShopFollower.objects.filter(
            user=request.user, shop=ad.shop
        ).exists()
    cart_product_form = CartAddProductForm()
    return render(request, 'home/detail.html', {'ad':ad,'adsimage':adsimage, 'ad_similar':ad_similar,
                                               'profile':profile,'latests':latests,'is_favourite': is_favourite,
                                                'categories': categories,'cart_product_form': cart_product_form,
                                                'rating':rating, 'user_rating':user_rating,'reviews':reviews,
                                                'affiliates':affiliates, 'is_shop_subscribed': is_shop_subscribed})
@login_required
def ads_favourite_list(request):
    user = request.user
    favourites = user.favourite.all()
    for product in favourites:
        WishlistItem.objects.get_or_create(user=user, product=product)
    wishlist_items = WishlistItem.objects.filter(user=user).select_related("product")
    notifications = (
        WishlistNotification.objects.filter(user=user)
        .select_related("product")
        .order_by("-created_at")[:10]
    )
    context = {
        'wishlist_items': wishlist_items,
        'notifications': notifications,
    }
    return render(request, 'owner/bookmarked.html', context)

@login_required
def favourite_ad(request, id):
    ad = get_object_or_404(Products, id=id)
    print(ad)
    if ad.favourite.filter(id=request.user.id).exists():
        ad.favourite.remove(request.user)
        WishlistItem.objects.filter(user=request.user, product=ad).delete()
    else:
        ad.favourite.add(request.user)
        WishlistItem.objects.get_or_create(user=request.user, product=ad)

    return HttpResponseRedirect(ad.get_absolute_url())

@login_required
def favourite_delete(request, id):
    ad = get_object_or_404(Products, id=id)
    print(ad)
    if ad.favourite.filter(id=request.user.id).exists():
        ad.favourite.remove(request.user)
        WishlistItem.objects.filter(user=request.user, product=ad).delete()
    else:
        ad.favourite.add(request.user)
        WishlistItem.objects.get_or_create(user=request.user, product=ad)

    return redirect('home:favourites')


@login_required
@require_POST
def favourite_ads(request):
    ad = get_object_or_404(Products, id=request.POST.get('id'))
    is_favourite = False
    if ad.favourite.filter(id=request.user.id).exists():
        ad.favourite.remove(request.user)
        WishlistItem.objects.filter(user=request.user, product=ad).delete()
        is_favourite = False
    else:
        ad.favourite.add(request.user)
        WishlistItem.objects.get_or_create(user=request.user, product=ad)
        is_favourite = True
    context = {
        'ad': ad,
        'is_favourite': is_favourite,
    }
    if request.is_ajax():
        html = render_to_string('home/special_section.html',context, request=request)
        return JsonResponse({'form': html})


@login_required
@require_POST
def update_wishlist_preferences(request, item_id):
    item = get_object_or_404(WishlistItem, id=item_id, user=request.user)
    item.notify_on_restock = bool(request.POST.get("notify_on_restock"))
    item.notify_on_price_drop = bool(request.POST.get("notify_on_price_drop"))
    item.save(update_fields=["notify_on_restock", "notify_on_price_drop"])
    messages.success(request, "Wishlist alert preferences updated.")
    return redirect("home:favourites")


@login_required
@require_POST
def toggle_shop_subscription(request, shop_id):
    shop = get_object_or_404(Shop, id=shop_id)
    if request.user.role != "customer":
        messages.error(request, "Only customers can subscribe to shops.")
        return redirect(request.META.get("HTTP_REFERER", "home:home"))
    if shop.owner_id == request.user.id:
        messages.error(request, "You cannot subscribe to your own shop.")
        return redirect(request.META.get("HTTP_REFERER", "home:home"))

    subscription, created = ShopFollower.objects.get_or_create(user=request.user, shop=shop)
    if created:
        messages.success(request, f"Subscribed to {shop.name}.")
    else:
        subscription.delete()
        messages.info(request, f"Unsubscribed from {shop.name}.")
    return redirect(request.META.get("HTTP_REFERER", "home:home"))


@login_required
def shop_notifications(request):
    notifications = (
        ShopNotification.objects.filter(user=request.user)
        .select_related("shop", "product")
        .order_by("-created_at")
    )
    ShopNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return render(request, "home/shop_notifications.html", {"notifications": notifications})


@login_required
def delete_post(request,pk=None):
    ad = Products.objects.get(id=pk)
    if request.user != ad.shop.owner:
        raise Http404()
    ad.delete()
    messages.success(request, "You property has been successfuly deleted")
    return redirect('home:my_aids')

def customer_list(request):
    customers_list = Profile.objects.all()
    query = request.GET.get('q')
    if query:
        customers_list = customers_list.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query)
        )
    paginator = Paginator(customers_list, 6)
    page_request_var = "page"
    page = request.GET.get('page')
    try:
        customers = paginator.page(page)
    except PageNotAnInteger:
        customers = paginator.page(1)
    except EmptyPage:
        customers = paginator.page(paginator.num_pages)
    return render(request, 'home/customer_list.html', {'customers':customers})

def submit_review(request, post_id):
    url = request.META.get("HTTP_REFERER")
    if request.method == "POST":
        try:
            reviews = ReviewRating.objects.get(
                user__user__id=request.user.id, post__id=post_id
            )
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, "Your review has been updated.")
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data["subject"]
                data.rating = form.cleaned_data["rating"]
                data.review = form.cleaned_data["review"]
                data.ip = request.META.get("REMOTE_ADDR")
                data.post_id = post_id
                data.user_id = request.user.profile.id
                data.save()
                messages.success(request, "Thank you! Your review has been submitted.")
                return redirect(url)

def category_count(request):
    counts = Products.objects.all().values('category__name').annotate(total=Count('category'))
    lates = Products.objects.order_by('-created_date')[:3]
    return render(request, 'home/footer.html', {'counts': counts, 'lates':lates})
