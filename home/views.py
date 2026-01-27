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

from account.models import Profile, User
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from blog.models import Post
from cart.forms import CartAddProductForm
from django.views.decorators.http import require_POST
from order.models import OrderItem, Order
from star_ratings.models import Rating
from star_ratings.models import UserRating

from owner.models import Affiliate


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

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        ads = ads.filter(category=category)
    return render(request,'home/index.html', {'category': category,'categories': categories,'ads': ads,'ads_veg':ads_veg,
                                              'ads_fruits':ads_fruits,'ads_grains':ads_grains,'ads_seafood':ads_seafood,
                                              'ads_spices':ads_spices,'latests':latests,
                                              'queryset': qs,'subcategories':subcategories,'queryset_list':queryset_list,'affiliates':affiliates})

def ads_list(request, category_slug=None):
    category = None
    ad_list = Products.objects.filter(available=True)
    order = request.GET.get('order', '-created_date')
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
    return render(request,'home/product_list.html', {'category': category,'categories': categories,'ads': ads,'latests':latests,
                                              'queryset': qs,'is_favourite': is_favourite,'order': order,'page': page,'affiliates':affiliates})

# admin ad list
def allads_list(request, category_slug=None):
    category = None
    ad_list = Products.objects.all().order_by('-created_at', '?')
    categories = Category.objects.all()
    states = Products.objects.all()
    query = request.GET.get('q')
    if query:
        ad_list = ad_list.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(phone=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query)
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
    profile = Profile.objects.get(user=ad.profile.user)
    categories = Category.objects.all()
    reviews = ReviewRating.objects.filter(post_id=ad.id, status=True)
    affiliates = Affiliate.objects.all()[:10]
    try:
        rating = Rating.objects.get(object_id=ad.id)
    except Rating.DoesNotExist:
        rating = None
    user_rating = UserRating.objects.filter(rating__object_id=ad.id)
    is_favourite = False

    if ad.favourite.filter(id=request.user.id).exists():
        is_favourite = True
    cart_product_form = CartAddProductForm()
    return render(request, 'home/detail.html', {'ad':ad,'adsimage':adsimage, 'ad_similar':ad_similar,
                                               'profile':profile,'latests':latests,'is_favourite': is_favourite,
                                                'categories': categories,'cart_product_form': cart_product_form,
                                                'rating':rating, 'user_rating':user_rating,'reviews':reviews,'affiliates':affiliates})
@login_required
def ads_favourite_list(request):
    user = request.user
    favourite_posts = user.favourite.all()
    context = {
        'favourite_posts': favourite_posts,
    }
    return render(request, 'owner/bookmarked.html', context)

@login_required
def favourite_ad(request, id):
    ad = get_object_or_404(Products, id=id)
    print(ad)
    if ad.favourite.filter(id=request.user.id).exists():
        ad.favourite.remove(request.user)
    else:
        ad.favourite.add(request.user)

    return HttpResponseRedirect(ad.get_absolute_url())

@login_required
def favourite_delete(request, id):
    ad = get_object_or_404(Products, id=id)
    print(ad)
    if ad.favourite.filter(id=request.user.id).exists():
        ad.favourite.remove(request.user)
    else:
        ad.favourite.add(request.user)

    return redirect('home:favourites')


@login_required
@require_POST
def favourite_ads(request):
    ad = get_object_or_404(Products, id=request.POST.get('id'))
    is_favourite = False
    if ad.favourite.filter(id=request.user.id).exists():
        ad.favourite.remove(request.user)
        is_favourite = False
    else:
        ad.favourite.add(request.user)
        is_favourite = True
    context = {
        'ad': ad,
        'is_favourite': is_favourite,
    }
    if request.is_ajax():
        html = render_to_string('home/special_section.html',context, request=request)
        return JsonResponse({'form': html})


@login_required
def delete_post(request,pk=None):
    ad = Products.objects.get(id=pk)
    if request.user != ad.profile.user:
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


