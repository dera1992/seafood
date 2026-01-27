from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_list, name='home'),
    path('category_chart/', views.category_chart, name='category_chart'),
    path('ads_list', views.ads_list, name='ads_list'),
    path('allads_list', views.allads_list, name='allads_list'),
    path('customer_list', views.customer_list, name='customer_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('favourites/', views.ads_favourite_list, name="favourites"),
    path('favourite_ads/', views.favourite_ads, name="favourite_ads"),
    path('<slug:category_slug>/', views.ads_list, name='ads_list_by_category'),
    path('delete_post/(<pk>\d+)/', views.delete_post, name='delete_post'),
    path('<int:id>/favourite_ad/',views.favourite_ad, name='favourite_ad'),
    path('<int:id>/favourite_delete/',views.favourite_delete, name='favourite_delete'),
    path('<int:id>/<slug:slug>/', views.ad_detail, name='ad_detail'),
    path('category_count/',views.category_count,name='category_count'),
    path("submit_review/<int:post_id>/", views.submit_review, name="submit_review"),

]