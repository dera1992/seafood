from django.apps import AppConfig


class FoodcreateConfig(AppConfig):
    name = 'foodCreate'

    def ready(self):
        from . import signals  # noqa: F401
