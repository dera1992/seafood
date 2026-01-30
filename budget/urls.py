from django.urls import path

from . import views

app_name = 'budget'

urlpatterns = [
    path('', views.budget_dashboard, name='budget-dashboard'),
    path('create/', views.set_budget, name='set-budget'),
    path('<int:budget_id>/', views.view_budget, name='view-budget'),
    path('<int:budget_id>/add-item/', views.add_to_budget, name='add-item'),
    path('<int:budget_id>/remove-item/<int:item_id>/', views.remove_from_budget, name='remove-item'),
    path('<int:budget_id>/from-cart/', views.add_from_cart, name='add-from-cart'),
    path('<int:budget_id>/duplicate/', views.duplicate_budget, name='duplicate-budget'),
]
