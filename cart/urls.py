from django.urls import path
from . import views
from .views import (
    OrderSummaryView
)


app_name = 'cart'

urlpatterns = [

  path('', views.cart_detail, name='cart_detail'),
  path('add/<int:product_id>/',views.cart_add,name='cart_add'),
  path('remove/<int:product_id>/',views.cart_remove,name='cart_remove'),
  path('add_to_cart/<slug>/', views.add_to_cart, name='add_to_cart'),
  path('add_to_cart_ajax/', views.add_to_cart_ajax, name='add_to_cart_ajax'),
  path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
#    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
  path('remove_from_cart/<slug>/', views.remove_from_cart, name='remove_from_cart'),
  path('remove_item_from_cart/<slug>/', views.remove_single_item_from_cart,
         name='remove_single_item_from_cart'),

]