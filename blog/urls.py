from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('blog/', views.post_list, name='list'),
    path('create/', views.post_create, name='post_create'),
    path('(<id>\d+)/<slug>[\w-]+/', views.post_detail, name='post_detail'),
    path('<slug>[\w-]+/edit/', views.post_update, name='update'),
    path('<slug>[\w-]+/delete/', views.post_delete, name='post_delete'),

]