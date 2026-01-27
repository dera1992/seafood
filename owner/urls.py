from django.urls import path
from . import views

app_name = 'owner'

urlpatterns = [
    path('my_cart/', views.my_cart, name='my_cart'),
    path('bookmarked/', views.bookmarked, name='bookmarked'),
    path('delete_post/(<pk>\d+)/', views.delete_post, name='delete_post'),
    path('hide_post/(<pk>\d+)/', views.hide_post, name='hide_post'),
    path('create_contact/', views.create_contact, name='create_contact'),
    path('about_us/', views.about_us, name='about_us'),
    path('faq/', views.faq, name='faq'),
    path('success/', views.success, name='success'),
    path('failure/', views.failure, name='failure'),

]