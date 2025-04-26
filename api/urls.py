from django.urls import path

from .views import (
    SensorListAPIView,  # Optional: For listing sensors
    SensorDataTempListAPIView,  # Optional: For listing temperature data
    SensorDataAirListAPIView,  # Optional: For listing air data
    SensorDataIndoorListAPIView,  # Optional: For listing indoor data
)

urlpatterns = [
    path('sensors/', SensorListAPIView.as_view(), name='list-sensors'),
    path('sensors/temperature/data/', SensorDataTempListAPIView.as_view(), name='list-temp-data'),
    path('sensors/air/data/', SensorDataAirListAPIView.as_view(), name='list-air-data'),
    path('sensors/indoor/data/', SensorDataIndoorListAPIView.as_view(), name='list-indoor-data'),
]
