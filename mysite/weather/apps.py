from django.apps import AppConfig


class WeatherConfig(AppConfig):
    name = 'weather'

    def ready(self):
        from . import schedule
        schedule.start()
