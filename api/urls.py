from django.urls import path

from .views import (
    SensorListCreateAPIView,  # For getting the last temperature data
    SensorDataTempListCreateAPIView,
    SensorDataAirListCreateAPIView,
    SensorDataIndoorListCreateAPIView
)

urlpatterns = [
    path('sensors/', SensorListCreateAPIView.as_view(), name='sensors'),
    path('sensors/temperature/data/', SensorDataTempListCreateAPIView.as_view(), name='temp-data'),
    path('sensors/air/data/', SensorDataAirListCreateAPIView.as_view(), name='air-data'),
    path('sensors/indoor/data/', SensorDataIndoorListCreateAPIView.as_view(), name='indoor-data'),

]
