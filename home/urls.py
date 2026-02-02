from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_list, name='home'),
    path('category_chart/', views.category_chart, name='category_chart'),
    path('shops/', views.shop_list, name='shop_list'),
    path('shops/<int:shop_id>/', views.shop_detail, name='shop_detail'),
    path('ads_list', views.ads_list, name='ads_list'),
    path('allads_list', views.allads_list, name='allads_list'),
    path('customer_list', views.customer_list, name='customer_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('analytics/customer/', views.customer_analytics, name='customer_analytics'),
    path('analytics/dispatcher/', views.dispatcher_analytics, name='dispatcher_analytics'),
    path('analytics/shop/', views.shop_analytics, name='shop_analytics'),
    path('nearby_shops/', views.nearby_shops, name='nearby_shops'),
    path('favourites/', views.ads_favourite_list, name="favourites"),
    path('favourite_ads/', views.favourite_ads, name="favourite_ads"),
    path(
        "wishlist/<int:item_id>/preferences/",
        views.update_wishlist_preferences,
        name="wishlist_preferences",
    ),
    path("shops/<int:shop_id>/subscribe/", views.toggle_shop_subscription, name="toggle_shop_subscription"),
    path("shop-notifications/", views.shop_notifications, name="shop_notifications"),
    path('products/<int:id>/<slug:slug>/preview/', views.ad_preview, name='ad_preview'),
    path('<slug:category_slug>/', views.ads_list, name='ads_list_by_category'),
    path('delete_post/(<pk>\d+)/', views.delete_post, name='delete_post'),
    path('<int:id>/favourite_ad/',views.favourite_ad, name='favourite_ad'),
    path('<int:id>/favourite_delete/',views.favourite_delete, name='favourite_delete'),
    path('<int:id>/<slug:slug>/', views.ad_detail, name='ad_detail'),
    path('category_count/',views.category_count,name='category_count'),
    path("submit_review/<int:post_id>/", views.submit_review, name="submit_review"),

]
