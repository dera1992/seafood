from django.urls import path

from . import views

app_name = "chat"

urlpatterns = [
    path("", views.inbox, name="inbox"),
    path("thread/<int:shop_id>/<int:user_id>/", views.thread, name="thread"),
    path(
        "thread/<int:shop_id>/<int:user_id>/messages/",
        views.thread_messages,
        name="thread_messages",
    ),
    path("send/", views.send_message, name="send_message"),
]
