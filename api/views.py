from rest_framework import generics

from core.models import Sensor, SensorDataTemp, SensorDataAir, SensorDataIndoor
from .serializers import (
    SensorSerializer,
    SensorDataTempSerializer,
    SensorDataAirSerializer,
    SensorDataIndoorSerializer,
)


class SensorListCreateAPIView(generics.ListCreateAPIView):
    queryset = Sensor.objects.all().order_by('id')
    serializer_class = SensorSerializer


class SensorDataTempListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataTemp.objects.all().order_by('-time')
    serializer_class = SensorDataTempSerializer


class SensorDataAirListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataAir.objects.all().order_by('-time')
    serializer_class = SensorDataAirSerializer


class SensorDataIndoorListCreateAPIView(generics.ListCreateAPIView):
    queryset = SensorDataIndoor.objects.all().order_by('-time')
    serializer_class = SensorDataIndoorSerializer

class SensorDataTempLatestAPIView(generics.RetrieveAPIView):
    serializer_class = SensorDataTempSerializer
    pagination_class = None  # Disable pagination for this view

    def get_object(self):
        sensor_id = self.kwargs.get('sensor_id')
        return SensorDataTemp.objects.filter(
            sensor_id=sensor_id
        ).order_by('-time').first()