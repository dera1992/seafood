from django.urls import path

from . import views
from .views import (
    CheckoutView,
    PaymentView,
    AddCouponView,

)

app_name = 'order'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('ajax/load-cities/', views.load_cities, name='ajax_load_cities'),  # <-- this one here
    path('order_all/', views.order_all, name='order_all'),
    path('order_owner/', views.order_owner, name='order_owner'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('transfer/', views.transfer, name='transfer'),
    path('tracking/', views.order_tracking, name='tracking'),
    path('tracking/<str:ref>/', views.order_tracking, name='tracking_detail'),
    path('status/<int:order_id>/', views.update_order_status, name='update_status'),
    path('<str:ref>/', views.verify_payment, name='verify_payment'),

]
