from django.urls import path
from . import views

app_name = 'foodCreate'

urlpatterns = [
    path('edit_post/(<pk>\d+)/', views.editAd, name='edit_post'),
    path('post/', views.postAd, name='post'),
    path('ajax/load-subcategories/', views.load_subcategories, name='ajax_load_subcategories'),  # <-- this one here
]
