from django.urls import path

from .views import (
    SensorDataTempCreateView,
    SensorDataAirCreateView,
    SensorDataIndoorCreateView,
    SensorListAPIView,  # Optional: For listing sensors
    SensorDataTempListAPIView,  # Optional: For listing temperature data
    SensorDataAirListAPIView,  # Optional: For listing air data
    SensorDataIndoorListAPIView,  # Optional: For listing indoor data
    LastSensorDataTempAPIView,  # Optional: For getting the last temperature data
)

urlpatterns = [
    path('sensors/temperature/', SensorDataTempCreateView.as_view(), name='create-temp-data'),
    path('sensors/air/', SensorDataAirCreateView.as_view(), name='create-air-data'),
    path('sensors/indoor/', SensorDataIndoorCreateView.as_view(), name='create-indoor-data'),
    # Optional endpoints for listing data (for debugging or other purposes)
    path('sensors/', SensorListAPIView.as_view(), name='list-sensors'),
    path('sensors/temperature/data/', SensorDataTempListAPIView.as_view(), name='list-temp-data'),
    path('sensors/air/data/', SensorDataAirListAPIView.as_view(), name='list-air-data'),
    path('sensors/indoor/data/', SensorDataIndoorListAPIView.as_view(), name='list-indoor-data'),
    path('sensors/<int:sensor_id>/temperature/last/', LastSensorDataTempAPIView.as_view(), name='last-temp-data'),

]
