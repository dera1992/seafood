from django.urls import path

from . import views

app_name = 'budget'

urlpatterns = [
    path('', views.budget_dashboard, name='budget-dashboard'),
    path('create/', views.set_budget, name='set-budget'),
    path('products/autocomplete/', views.product_autocomplete, name='product-autocomplete'),
    path('<int:budget_id>/', views.view_budget, name='view-budget'),
    path('<int:budget_id>/add-item/', views.add_to_budget, name='add-item'),
    path('<int:budget_id>/items/<int:item_id>/edit/', views.edit_budget_item, name='edit-item'),
    path('<int:budget_id>/items/<int:item_id>/quantity/', views.update_budget_item_quantity, name='update-item-quantity'),
    path('<int:budget_id>/remove-item/<int:item_id>/', views.remove_from_budget, name='remove-item'),
    path('<int:budget_id>/from-cart/', views.add_from_cart, name='add-from-cart'),
    path('<int:budget_id>/duplicate/', views.duplicate_budget, name='duplicate-budget'),
    path('<int:budget_id>/templates/create/', views.create_template, name='create-template'),
    path('<int:budget_id>/templates/<int:template_id>/apply/', views.apply_template, name='apply-template'),
    path('templates/<int:template_id>/', views.view_template, name='view-template'),
    path('templates/<int:template_id>/add-item/', views.add_template_item, name='add-template-item'),
    path('templates/<int:template_id>/remove-item/<int:item_id>/', views.remove_template_item, name='remove-template-item'),
]
