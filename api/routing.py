from django.urls import path
from .consumers import SensorDataConsumer

websocket_urlpatterns = [
    path('ws/sensor_data/<int:sensor_id>/', SensorDataConsumer.as_asgi()),
]