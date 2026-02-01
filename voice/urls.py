from django.urls import path

from voice import views

app_name = "voice"

urlpatterns = [
    path("interpret/", views.interpret_voice, name="interpret"),
    path("search/", views.search_page, name="search"),
    path("budget/", views.budget_page, name="budget"),
]
