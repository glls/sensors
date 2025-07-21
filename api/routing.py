from django.urls import path

from .consumers import SensorsDataConsumer

websocket_urlpatterns = [
    path('ws/sensor_data/', SensorsDataConsumer.as_asgi()),
]
